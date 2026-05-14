import type { Result, User } from '../types';
import type { UserService } from '../services/userService';

interface HttpResponse {
  status: number;
  body: unknown;
}

/**
 * HTTP-style adapters for the user service. Each handler returns a plain
 * object describing the response — no framework coupling. The userId is
 * read from the request body for create, and from path params for the rest.
 */
export class UserController {
  constructor(private readonly service: UserService) {}

  create(body: User): HttpResponse {
    const result = this.service.create(body);
    return resultToHttp(result, 201);
  }

  get(params: { userId: string }): HttpResponse {
    const result = this.service.get(params.userId);
    return resultToHttp(result, 200);
  }

  remove(params: { userId: string }): HttpResponse {
    const removed = this.service.remove(params.userId);
    if (removed) {
      return { status: 204, body: null };
    }
    return { status: 404, body: { error: `not found: ${params.userId}` } };
  }
}

function resultToHttp<T>(result: Result<T>, successStatus: number): HttpResponse {
  if (result.ok) {
    return { status: successStatus, body: result.value };
  }
  return { status: 400, body: { error: result.error } };
}
