# Building Serverless Robotics — 1~24장 완주 가이드
## 다음 학습과 작업을 위한 마스터 문서
​
> 생성일: 2026-09-18
> 교재: Dmytro Kozhevin, Building Serverless Robotics with AWS, AI, and ROS 2
> 진도: 17장부터 시작 → 17~24 완주 → 1~16 메우기 → 93 passed
> GitHub ID: skchoi0815
> WSL Ubuntu 26.04 / Python 3.12.2 robocloud / Terraform v1.16.2 / Docker 29.1.3
​
---
​
## 0. 최종 상태 한눈에
[✅] pytest 93 passed in ~2.3s [✅] terraform validate Success! [✅] colcon BUILD_OK + hello_node ROS2 mode [✅] locust 8522 reqs 0% fail Med 0ms [✅] GitHub 4 repos push 완료

​
### GitHub 4개
​
| 로컬 | Remote | 마지막 | 내용 |
|---|---|---|---|
| ~/robocloud-test | skchoi0815/robocloud-test | f82b59e | 93 tests |
| ~/turret_ws | skchoi0815/turret_ws | 5ebcc68 | Ch9 BUILD_OK |
| ~/infra | skchoi0815/infra | ff76e0a | Ch2-5 dev wiring |
| ~/tf-modules | skchoi0815/tf-modules | e1246c8 | Ch3-5 모듈 |
​
### robocloud-test 커밋 순서

6a8e9e3 ch17-18: 17장 30 + 18장 11 (22 files, 첫 커밋) 9179af2 ch19: bearer token rotation 3 9064a9d ch19: EdgeIDS 4 76eb0bf ch19: incident response 2 - 4s contain b94995c ch20: dynamodb sharding 3 68d93cb ch20: lambda concurrency + s3 prefix 5 142d66e ch21: agent tools 4 - threat 100 9e8307b ch21: agent brain 4 - retry + human-in-loop 8e40fb9 ch22: selective vision 6 2349a24 ch22: 3d + flow 3 9002511 ch23: mesh + consensus + handoff 5 329069a ch24: field survival 6 99d11f3 ch8: FFT-lite 2 f82b59e ch12-14: fusion 2 + dashboard 3 (HEAD, 93 passed)

​
---
​
## 1. 환경 땅
​
### 1-1. 버전
​
- OS: Ubuntu 26.04 LTS resolute on WSL2
- system python: 3.14.7 → Lambda 3.12와 안 맞음, 쓰지 않음
- pyenv: 3.12.2 + robocloud venv
- pytest 9.1.1, boto3 1.43.97, moto 5.2.3, locust 2.46.6
- Terraform v1.16.2, aws-cli 2.36.44 (NoCredentials)
- Docker 29.1.3, ROS osrf/ros:humble-desktop
​
### 1-2. PATH 꼬임 해결법
​
증상: `which -a python` 맨 앞이 miniforge3, `python --version` 3.14.7만 뜸
​
원인: ~/.bashrc에서 pyenv 블록이 conda 블록보다 앞에 있음. conda가 PATH 덮음.
​
정답 순서 (bashrc 맨 밑):
```bash
# <<< conda initialize <<< 먼저
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"  # 나중에

bash

conda config --set auto_activate false
exec bash  # 따로 실행! 뒤에 명령 붙이면 날아감
which -a python  # 맨 앞이 .pyenv/shims/python 이어야 함
pyenv global 3.12.2
1-3. robocloud 재현
bash

pyenv install 3.12.2
pyenv virtualenv 3.12.2 robocloud
mkdir -p ~/robocloud-test && cd ~/robocloud-test
pyenv local robocloud
pip install --upgrade pip wheel
pip install pytest boto3 moto locust websocket-client protobuf grpcio-tools numpy
1-4. ROS 재현
bash

# ros:humble-desktop는 없음. osrf/ 붙여야 함
docker pull osrf/ros:humble-desktop
docker run --rm -v ~/turret_ws:/root/turret_ws osrf/ros:humble-desktop bash -c "source /opt/ros/humble/setup.bash && echo \$ROS_DISTRO && cd /root/turret_ws && colcon build --packages-select thermal_tracker && echo BUILD_OK"
docker run --rm -v ~/turret_ws:/root/turret_ws osrf/ros:humble-desktop bash -c "source /opt/ros/humble/setup.bash && source /root/turret_ws/install/setup.bash && timeout 5 ros2 run thermal_tracker hello_node || true"
# 기대: humble, BUILD_OK, ROS2 mode
2. 디렉토리 구조
~/robocloud-test/ (.python-version = robocloud)
 proto/robotics_messages_v2.proto
 robotics_messages_v2_pb2.py
 credential_vendor.py / test_credential_vendor.py (Ch3, 5)
 websocket_handler.py / test_websocket_handler.py (Ch5, 5)
 presigned_url_handler.py / test_presigned_urls.py (Ch6, 7)
 protobuf_codec.py / test_protobuf_codec.py (Ch7, 6)
 test_integration_upload_pipeline.py (Ch4, 2)
 locustfile.py
 test_ros_logic.py (Ch10/11, 5)
 chaos_monkey.py
 device_registry.py / test_registry.py (4)
 ota_manager.py / test_ota_manager.py (4)
 health_monitor.py / test_health.py (3)
 token_rotation.py / test_token_rotation.py (3)
 edge_ids.py / test_edge_ids.py (4)
 incident_response.py / test_incident_response.py (2)
 dynamodb_scaling.py / test_scaling.py (3)
 lambda_scaling.py / s3_optimization.py / test_scale_out.py (5)
 agent_tools.py / test_agent_tools.py (4)
 agent_brain.py / test_agent_brain.py (4)
 vision_pipeline.py / test_vision.py (6)
 vision_3d.py / test_vision_3d.py (3)
 swarm_mesh.py / test_swarm.py (5)
 field_survival.py / test_field.py (6)
 audio_fft_lite.py / test_ch8_fft.py (2)
 fusion_lite.py / test_ch12_fusion.py (2)
 dashboard_lite.py / test_ch14_ops.py (3)
​
~/turret_ws/src/thermal_tracker/
 package.xml, setup.py, setup.cfg, resource/thermal_tracker
 thermal_tracker/__init__.py, hello_node.py, tracker_core.py, tracking_node.py, spotlight_node.py
​
~/infra/dev/main.tf
~/tf-modules/dynamodb-device-inventory, s3-event-store, sns-event-topic,
 sqs-processor-queue, dynamodb-results-table, lambda-event-processor,
 apigw-websocket, dynamodb-simple, lambda-simple
​
~/lambda-functions/audio-processor, ws-authorizer, ws-connect, ws-disconnect, ws-message

3. 테스트 93개 지도
bash

cd ~/robocloud-test
pyenv local robocloud
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test pytest -q
# 93 passed
Ch3 5: 200+ASIA, unknown/inactive 403, wrong 401, no id 400
Ch5 5: connect put_item, disconnect delete, ping→pong HasField, 깨짐 400
Ch6 7: key {id}/{ulid}.jpg, AES256, ExpiresIn 300, type별 limit
Ch7 6: base64 string, JSON대비 <50%, oneof routing
Ch4 2: S3→SNS→SQS fanout, DDB write
Ch10/11 5: IoU 1.0/0, kalman 321, Pan±90 Tilt0-60, 30프레임 삭제
Ch18 Registry 4: ONLINE, telemetry, OFFLINE, HIGH_TEMP
Ch18 OTA 4: canary 1대 threshold100, staged 4단계, dry SUCCESS, rollback
Ch18 Health 3: 100 HEALTHY, 75도 remediation, OFFLINE CRITICAL
Ch19 Token 3: 없음→True, 256bit, REVOKED→True
Ch19 EdgeIDS 4: OK/VIOLATED, xmrig KILL, 지문 False
Ch19 Incident 2: CONTAINED 4s, REVOKED
Ch20 Sharding 3: 100대 분산, 같은놈 같은shard
Ch20 ScaleOut 5: reserved 500<800, batch25/conc50, prefix>10
Ch21 Tools 4: active 1개, threat 100 ENGAGE, SUCCESS, 미접속 ERROR
Ch21 Brain 4: Throttling 3번 재시도, human 판정
Ch22 Vision 6: 0.96 track, 0.73 enhance, both 합치기
Ch22 3D 3: 40px=7m 8px=35m, flow +1px
Ch23 Swarm 5: TTL죽음, loop방지, 가중평균, feature 없으면 False
Ch24 Field 6: SOC, full/normal/economy/survival, humidity CRITICAL
Ch8 2: 200+400Hz 5dB↑, 노이즈 <5dB
Ch12 2: 라인거리 0, 각도wrap 20도
Ch14 3: HIGH_THREAT, fused parse, 6555-198>6000
Load: locust 100users 30s → 8522 reqs 0% Med 0ms (로컬 CPU, 네트워크 아님)
Chaos: python chaos_monkey.py → [DRY RUN] Order restored (돈 안 나감)
4. Terraform 지도
bash

cd ~/infra/dev
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test terraform init
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test terraform validate
# Success! The configuration is valid.
고친 함정:

한줄 HCL 금지. 줄바꿈+콤마 필수
S3 lifecycle filter {} 필수
WebSocket route_selection_expression = "$default" (base64는 $request.body.action 못 읽음)
identity_sources = [header, querystring] 둘 다
DynamoDB float 금지 → Decimal('0.3') 문자열로
SQS visibility >= Lambda timeout +30s
WSS→HTTPS: wss:// → https:// 바꿔서 apigatewaymanagementapi 만들기
5. 장별 교훈 한줄
17장 DEVICE_REGION=None 4시간 실명 → 시작하자마자 검증
18장 3:47am TURRET-045~052 전멸 → canary 1대 threshold100
19장 2:14am Jake 노트북 → 24h 만료 + REVOKED, 피해 $0
20장 312 WALL → hour#shard 10개 + reserved 500/800 + S3 256 shards
21장 trk-d9e8 threat 100 turret-04 4.2s → 물리명령은 human
22장 8px 73%→enhance→96%, 풀파이프 313ms라 골라서 25FPS
23장 4.7초 유령 1드론 2트랙 → feature까지 봐야 confirm
24장 Submarine 31 → 10.5V survival, 데이터 로컬저장
Ch1 
8.72
/
d
a
y
→
C
h
24
0.04/day 217배
6. 다음 작업
A. 실전 배포 (SSO 필요)
bash

aws configure sso
aws sso login --profile frontline
export AWS_PROFILE=frontline
# infra/dev/main.tf backend S3로 변경 후 plan → apply (돈 나감, plan까지만 권장)
B. 심화
Ch8 scipy + RandomForest pkl S3
Ch10 ultralytics YOLO (Jetson 필요)
Ch14 React dashboard + WebSocketManager.ts
Ch16 CloudWatch + X-Ray
C. 매일 운영
bash

cd ~/robocloud-test && AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test pytest -q
cd ~/infra/dev && AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test terraform validate
git status --short
7. 트러블슈팅
증상	해결
3.14만 뜸	bashrc conda→pyenv 순서, pyenv global 3.12.2
ros2 not found	osrf/ros:humble-desktop Docker
ros:humble-desktop not found	osrf/ 붙이기
Float not supported	Decimal('0.3')
Missing attribute separator	한줄 HCL 줄바꿈
filter required	filter {} 추가
NoCredentials	AWS_ACCESS_KEY_ID=test 붙이기
exec bash 뒤 날아감	따로 실행
~/path/ Is a directory	ls ~/path/ 로 치기
8. 10초컷 검증
bash

cd ~/robocloud-test && pyenv local robocloud && AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test pytest -q
cd ~/infra/dev && AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test terraform validate
docker run --rm -v ~/turret_ws:/root/turret_ws osrf/ros:humble-desktop bash -c "source /opt/ros/humble/setup.bash && cd /root/turret_ws && colcon build --packages-select thermal_tracker && echo BUILD_OK"
Go Build Something That Matters. Mud is waiting.
