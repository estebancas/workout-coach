# TrueCoach API notes

Undocumented API behind the web client at `https://pr4mathletics.truecoach.co`. Found by reading the web app, not from official docs.

## Auth
- `POST /proxy/api/oauth/token`, form-encoded `grant_type=password`, `username`, `password`. Returns `access_token`, `token_type`, `user_id`. No `expires_in`, no refresh token.
- `POST /proxy/api/oauth/destroy` revokes a token.
- A bad or missing token returns 401 "Unable to find a logged in user with the given token".
- Every call needs `Authorization: Bearer <token>` **and** `Role: Client` (capital C). Without the role header the API returns a misleading 404 "Unable to find a matching client".

## Endpoints
- `GET /proxy/api/users/me`: `clients[0].id` is the client id; `user` has `first_name` and `last_name`.
- `GET /proxy/api/clients/<id>/workouts?order=asc&page=1&per_page=50&states=pending`

## Workouts response
Keys: `workouts[]`, `workout_items[]`, `comments[]`, `meta`.
- `meta`: `page`, `total_pages`, `per_page`, `total_count`.
- Workout: `id`, `due` (YYYY-MM-DD), `title`, `state`, `warmup`, `cooldown`, `rest_day`, `short_description`, `program_name`, `workout_item_ids`, and more.
- Workout item: `workout_id`, `name`, `info` (free text such as "3x15 por lado"), `position`, `is_circuit`, `linked`. Items are flat and unordered, so sort by `position` within a workout.
- `states=pending` returns only upcoming days (about two weeks ahead). `states=pending,completed` or no filter returns years of history, oldest first. There is no date filter that we know of, so `fetch` paginates and filters on `due` client-side.

## Snapshots
`workout-coach fetch` saves the raw filtered response to `data/snapshots/<from>_<to>_<utc stamp>.json`. That folder is gitignored, because it holds personal training data. Curated fixtures for evals will be copied elsewhere in Phase 10.
