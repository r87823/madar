import 'package:flutter/material.dart';

import '../core/api/frappe_api_client.dart';
import '../core/auth/auth_controller.dart';
import '../features/attendance/attendance_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/accounting/erp_sync_review_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/delivery/dispatch_queue_screen.dart';
import '../features/orders/approval_queue_screen.dart';
import '../features/orders/order_list_screen.dart';
import '../features/production/production_mapping_screen.dart';
import '../features/production/work_order_list_screen.dart';

class MadarApp extends StatefulWidget {
  const MadarApp({super.key});

  @override
  State<MadarApp> createState() => _MadarAppState();
}

class _MadarAppState extends State<MadarApp> {
  late final AuthController _authController;
  late final FrappeApiClient _apiClient;

  @override
  void initState() {
    super.initState();
    _apiClient = FrappeApiClient(baseUri: FrappeApiClient.staging);
    _authController = AuthController(apiClient: _apiClient);
  }

  @override
  void dispose() {
    _authController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Madar',
      debugShowCheckedModeBanner: false,
      locale: const Locale('ar'),
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1E6F68)),
        scaffoldBackgroundColor: const Color(0xFFF6F8F7),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
          fillColor: Colors.white,
        ),
        cardTheme: const CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
        ),
      ),
      builder: (context, child) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: child ?? const SizedBox.shrink(),
        );
      },
      home: AnimatedBuilder(
        animation: _authController,
        builder: (context, _) {
          final currentContext = _authController.context;
          if (currentContext == null) {
            return LoginScreen(controller: _authController);
          }
          return DashboardScreen(
            context: currentContext,
            onLogout: _authController.logout,
            onOpenAttendance: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => AttendanceScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenOrders: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => OrderListScreen(
                    apiClient: _apiClient,
                    userContext: currentContext,
                  ),
                ),
              );
            },
            onOpenApprovalQueue: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ApprovalQueueScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenErpSyncReview: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ErpSyncReviewScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenProductionMappings: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) =>
                      ProductionMappingScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenWorkOrders: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => WorkOrderListScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenDispatchQueue: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DispatchQueueScreen(apiClient: _apiClient),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
