# 18 Legacy PHP API Client Migration

Legacy PHP API client migration task. The model must repair a TypeScript payment gateway port so it preserves operational behavior while using an injected client.

The hidden checks cover idempotency key construction, metadata carry-over, recoverable decline mapping, injected-client usage and avoiding mutation of caller-owned request objects.
