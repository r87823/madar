# Madar / مدار

Madar is a Frappe custom app with a Flutter client foundation.

## Flutter Client

The Flutter app is Arabic-first and talks only to the Madar/Frappe backend:

- Login: `POST /api/method/login`
- Current context: `GET /api/method/madar.api.me.get_context`
- Logout: `GET /api/method/logout`

It does not call ERPNext DocTypes directly and does not store ERPNext credentials.

Useful local checks:

```bash
flutter analyze
flutter test
flutter run -d macos
flutter run -d chrome
```
