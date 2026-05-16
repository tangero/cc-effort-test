# Task 07: Security Audit

## Popis

TypeScript Express API se 5 bezpečnostními chybami různé obtížnosti. Model musí najít a opravit všechny chyby, přičemž visible testy musí nadále procházet.

## Soubor k opravě

`src/routes/users.ts`

## Bezpečnostní chyby

| # | Typ | Obtížnost | Popis |
|---|-----|-----------|-------|
| 1 | SQL Injection | zřejmá | `GET /search` — username přímo do SQL |
| 2 | SQL Injection | zřejmá | `POST /login` — credentials přímo do SQL |
| 3 | Sensitive Data Exposure | střední | `GET /:id` — vrací i sloupec `password` |
| 4 | Reflected XSS | střední | `POST /register` — chybová zpráva jako raw HTML |
| 5 | Mass Assignment | skrytá | `PUT /:id` — `role` přijímána z request body |

## Effort diferenciace

- **Low effort**: Opraví zřejmé SQL injection (BUG 1, 2). Score: ~0.4
- **Medium effort**: Najde i password exposure a XSS (BUG 3, 4). Score: ~0.8
- **High effort**: Najde všechny včetně mass assignment (BUG 5). Score: 1.0

## Spuštění testů

```bash
cd initial_repo
npm install
npm test          # visible testy — musí projít s buggy kódem
```

## Verify

```bash
# Z adresáře workdir (rozbalená initial_repo):
bash /path/to/tasks/07_security_audit/verify.sh
```
