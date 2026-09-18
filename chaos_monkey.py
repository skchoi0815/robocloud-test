import random, time
class ChaosMonkey:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
    def unleash(self, duration_minutes=1):
        actions = [self.kill_random_lambda, self.throttle_dynamodb, self.fill_sqs_queue]
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Unleashing chaos...")
        for _ in range(3):
            a = random.choice(actions)
            print(f"\n Executing: {a.__name__}")
            a()
            time.sleep(1)
        print("\n Chaos test complete. Restoring order... Order restored.")
    def kill_random_lambda(self):
        print("  → [DRY] Disabling Lambda device-heartbeat-processor (concurrency=0 → restore)")
    def throttle_dynamodb(self):
        print("  → [DRY] Throttling DynamoDB device-fleet to 1 RCU/WCU → PAY_PER_REQUEST restore")
    def fill_sqs_queue(self):
        print("  → [DRY] Flooding SQS with 1000 msgs → DLQ check")
if __name__ == "__main__":
    ChaosMonkey(dry_run=True).unleash()
