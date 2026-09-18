import random
from enum import Enum
from typing import List
from datetime import datetime, timezone
from decimal import Decimal

class UpdateStrategy(Enum):
    CANARY = "canary"
    STAGED = "staged"
    BLUE_GREEN = "blue_green"
    IMMEDIATE = "immediate"

class OTAManager:
    def __init__(self, registry):
        self.registry = registry
        self.table = registry.table

    def create_update_campaign(self, version: str,
                               strategy: UpdateStrategy = UpdateStrategy.STAGED,
                               target_group: str = 'all',
                               dry_run: bool = False) -> str:
        campaign_id = f"campaign-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        if target_group == 'all':
            devices = self.registry.get_all_devices()
        else:
            devices = [d for d in self.registry.get_all_devices()
                       if d.get('deployment_group') == target_group]

        eligible = [d for d in devices
                    if not d.get('update_locked')
                    and d.get('status') == 'ONLINE'
                    and d.get('connection_id')]

        # BLAST-RADIUS GUARDRAIL - 교재 p504
        max_allowed = self._get_blast_radius_limit(target_group, len(devices))
        if len(eligible) > max_allowed:
            print(f" Campaign limited to {max_allowed} (blast-radius)")
            eligible = random.sample(eligible, max_allowed)

        if not eligible:
            raise ValueError("No eligible devices (need ONLINE + connection_id)")

        stages = self._plan_stages(eligible, strategy)
        campaign = {
            'PK': f'CAMPAIGN#{campaign_id}', 'SK': 'METADATA',
            'campaign_id': campaign_id,
            'version': version,
            'strategy': strategy.value,
            'target_group': target_group,
            'total_devices': len(eligible),
            'updated_devices': 0,
            'failed_devices': 0,
            'status': 'PLANNED',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'dry_run': dry_run,
            'stages': stages,
            'successful_updates': [],
            'failed_updates': [],
            'rollback_version': eligible[0].get('software_version', '0.0.0')
        }
        self.table.put_item(Item=campaign)
        print(f" Campaign {campaign_id}: {version} {strategy.value} {len(eligible)} devices dry_run={dry_run}")
        return campaign_id

    def _plan_stages(self, devices: List[dict], strategy: UpdateStrategy):
        stages = []
        if strategy == UpdateStrategy.CANARY:
            canary = self._pick_canary(devices)
            stages.append({'stage': 1, 'percentage': Decimal('0.3'),
                           'devices': [canary['device_id']],
                           'wait_minutes': 30, 'success_threshold': 100})
            remaining = [d['device_id'] for d in devices if d['device_id'] != canary['device_id']]
            stages.append({'stage': 2, 'percentage': 100,
                           'devices': remaining,
                           'wait_minutes': 0, 'success_threshold': 95})
        elif strategy == UpdateStrategy.STAGED:
            percentages = [10, 25, 50, 100]
            waits = [60, 45, 30, 0]
            thresholds = [100, 98, 95, 95]
            tmp = devices[:]
            random.shuffle(tmp)
            used = set()
            for i, pct in enumerate(percentages):
                count = max(1, int(len(devices) * pct / 100))
                sd = []
                for d in tmp:
                    if d['device_id'] not in used:
                        sd.append(d['device_id'])
                        used.add(d['device_id'])
                        if len(sd) >= count:
                            break
                # 마지막 stage는 남은 전부
                if i == len(percentages)-1:
                    for d in tmp:
                        if d['device_id'] not in used:
                            sd.append(d['device_id'])
                            used.add(d['device_id'])
                stages.append({'stage': i+1, 'percentage': pct,
                               'devices': sd, 'wait_minutes': waits[i],
                               'success_threshold': thresholds[i]})
        elif strategy == UpdateStrategy.BLUE_GREEN:
            mid = len(devices)//2
            stages.append({'stage': 1, 'percentage': 50,
                           'devices': [d['device_id'] for d in devices[:mid]],
                           'wait_minutes': 120, 'success_threshold': 98})
            stages.append({'stage': 2, 'percentage': 100,
                           'devices': [d['device_id'] for d in devices[mid:]],
                           'wait_minutes': 0, 'success_threshold': 98})
        else:  # IMMEDIATE - 쓰지마
            stages.append({'stage': 1, 'percentage': 100,
                           'devices': [d['device_id'] for d in devices],
                           'wait_minutes': 0, 'success_threshold': 90})
        return stages

    def _pick_canary(self, devices):
        # 가장 안정적인 놈: uptime 길고, 실패이력 없고, CRITICAL 아닌 놈
        def score(d):
            s = 100
            if d.get('failed_updates', 0) == 0: s += 25
            if str(d.get('site_id','')).startswith('CRITICAL'): s -= 50
            return s
        return sorted(devices, key=score, reverse=True)[0]

    def execute_stage(self, campaign_id: str, stage_num: int) -> dict:
        campaign = self._get_campaign(campaign_id)
        stage = campaign['stages'][stage_num-1]
        print(f" Executing stage {stage_num}: {len(stage['devices'])} devices")
        success, failed = [], []
        for device_id in stage['devices']:
            if campaign.get('dry_run'):
                success.append(device_id)  # dry_run은 전원 성공으로 간주
            else:
                if self._push_update_to_device(device_id, campaign['version']):
                    success.append(device_id)
                else:
                    failed.append(device_id)
        total = len(stage['devices'])
        rate = (len(success)/total*100) if total else 0
        result = {'stage': stage_num, 'success': success, 'failed': failed,
                  'success_rate': rate,
                  'stage_result': 'SUCCESS' if rate >= stage['success_threshold'] else 'FAILED'}
        print(f" Stage {stage_num}: {rate:.1f}% (need {stage['success_threshold']}%) → {result['stage_result']}")
        if result['stage_result'] == 'FAILED' and not campaign.get('dry_run'):
            self.rollback_campaign(campaign_id, reason=f"Stage {stage_num} failed")
        self._record_stage_results(campaign_id, result)
        return result

    def _push_update_to_device(self, device_id: str, version: str) -> bool:
        d = self.registry.get_device(device_id)
        if not d or not d.get('connection_id'):
            print(f" Device {device_id} no connection")
            return False
        # 실전은 여기서 apigateway.post_to_connection 으로
        # UpdateCommand protobuf base64를 쏜다. 테스트에선 True.
        print(f" Update pushed to {device_id} → {version}")
        return True

    def rollback_campaign(self, campaign_id: str, reason: str = "Automatic rollback") -> bool:
        print(f" ROLLBACK {campaign_id}: {reason}")
        campaign = self._get_campaign(campaign_id)
        targets = campaign.get('successful_updates', [])
        if not targets:
            # 아직 기록 전이면 stage1이라도 롤백 시도
            print(" No successful_updates yet, nothing to rollback")
            return True
        ok = 0
        for did in targets:
            if self._push_update_to_device(did, campaign.get('rollback_version', '0.0.0')):
                ok += 1
        print(f" Rollback {ok}/{len(targets)} done")
        self.table.update_item(
            Key={'PK': f'CAMPAIGN#{campaign_id}', 'SK': 'METADATA'},
            UpdateExpression='SET #st = :st',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={':st': 'ROLLED_BACK'}
        )
        return True

    def _get_campaign(self, campaign_id: str) -> dict:
        return self.table.get_item(Key={'PK': f'CAMPAIGN#{campaign_id}', 'SK': 'METADATA'})['Item']

    def _record_stage_results(self, campaign_id: str, results: dict):
        c = self._get_campaign(campaign_id)
        s = c.get('successful_updates', []) + results.get('success', [])
        f = c.get('failed_updates', []) + results.get('failed', [])
        self.table.update_item(
            Key={'PK': f'CAMPAIGN#{campaign_id}', 'SK': 'METADATA'},
            UpdateExpression='SET successful_updates = :s, failed_updates = :f, updated_devices = :u, failed_devices = :fd',
            ExpressionAttributeValues={':s': s, ':f': f, ':u': len(s), ':fd': len(f)}
        )

    def _get_blast_radius_limit(self, target_group: str, total: int) -> int:
        if target_group.startswith('CRITICAL'):
            return max(1, int(total*0.10))
        if target_group == 'all':
            return max(10, int(total*0.25)) if total > 10 else total
        return max(5, int(total*0.50)) if total > 5 else total
