---
trigger: model_decision
description: This rule explains the guidelines for writing Vitest tests for Next.js applications.
---

# Testing Guidelines

## Testing Framework

- `vitest` is used for testing
- Tests are colocated next to the tested file
  - Example: `dir/format.ts` and `dir/format.test.ts`

## Common Mocks

### Server-Only Mock

```ts
vi.mock("server-only", () => ({}));
```

### Prisma Mock

```ts
import { beforeEach } from "vitest";
import prisma from "@/utils/__mocks__/prisma";

vi.mock("@/utils/prisma");

describe("example", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("test", async () => {
    prisma.group.findMany.mockResolvedValue([]);
  });
});
```

## Best Practices

- Each test should be independent
- Use descriptive test names
- Mock external dependencies
- Clean up mocks between tests
- Avoid testing implementation details
