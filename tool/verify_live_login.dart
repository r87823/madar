import 'dart:io';

import 'package:madar/core/api/frappe_api_client.dart';

Future<void> main() async {
  final password = Platform.environment['MADAR_E2E_PASSWORD'];
  if (password == null || password.isEmpty) {
    stderr.writeln('MADAR_E2E_PASSWORD is required.');
    exitCode = 2;
    return;
  }

  final scenarios = {
    'driver.test@example.com': [
      'delivery.view_assigned_batches',
      'payments.collect',
      'cashbox.view_own',
    ],
    'accountant.test@example.com': ['accounting.view_sync_logs'],
    'branch.supervisor@example.com': ['orders.approve'],
  };

  for (final entry in scenarios.entries) {
    final client = FrappeApiClient(baseUri: FrappeApiClient.staging);
    await client.login(username: entry.key, password: password);
    final context = await client.getContext();
    final permissions = context.permissions.toSet();
    final missing = entry.value
        .where((permission) => !permissions.contains(permission))
        .toList();
    if (missing.isNotEmpty) {
      throw StateError(
        '${entry.key} missing permissions: ${missing.join(', ')}',
      );
    }
    if (context.employee == null) {
      throw StateError('${entry.key} did not return employee context');
    }
    stdout.writeln(
      '${entry.key}: permissions=${context.permissions.length}, '
      'branch=${context.branch?.name ?? 'none'}',
    );
    await client.logout();
  }
}
