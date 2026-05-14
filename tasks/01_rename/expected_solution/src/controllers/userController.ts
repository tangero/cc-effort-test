import type { Result, User } from '../types';
import type { UserService } from '../services/userService';

interface HttpResponse {
  status: number;
  body: unknown;
}

/**
 * HTTP-style adapters for the user service. Each handler returns a plain
 * object describing the response — no framework coupling. The accountId is
 * read from the request body for create, and from path params for the rest.
 */
export class UserController {
  constructor(private readonly service: UserService) {}

  create(body: User): HttpResponse {
    const result = this.service.create(body);
    return resultToHttp(result, 201);
  }

  get(params: { accountId: string }): HttpResponse {
    const result = this.service.get(params.accountId);
    return resultToHttp(result, 200);
  }

  remove(params: { accountId: string }): HttpResponse {
    const removed = this.service.remove(params.accountId);
    if (removed) {
      return { status: 204, body: null };
    }
    return { status: 404, body: { error: `not found: ${params.accountId}` } };
  }
}

function resultToHttp<T>(result: Result<T>, successStatus: number): HttpResponse {
  if (result.ok) {
    return { status: successStatus, body: result.value };
  }
  return { status: 400, body: { error: result.error } };
}
