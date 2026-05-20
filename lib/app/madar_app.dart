import 'package:flutter/material.dart';

import '../core/api/frappe_api_client.dart';
import '../core/auth/auth_controller.dart';
import '../core/auth/user_context.dart';
import '../features/attendance/attendance_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/accounting/erp_sync_review_screen.dart';
import '../features/cashbox/cashbox_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/delivery/delivery_batch_list_screen.dart';
import '../features/delivery/dispatch_queue_screen.dart';
import '../features/orders/approval_queue_screen.dart';
import '../features/orders/order_detail_screen.dart';
import '../features/orders/order_list_screen.dart';
import '../features/production/production_mapping_screen.dart';
import '../features/production/work_order_detail_screen.dart';
import '../features/production/work_order_list_screen.dart';
import '../features/notifications/notification_screen.dart';
import '../features/notifications/notification_models.dart';

class MadarApp extends StatefulWidget {
  const MadarApp({super.key});

  @override
  State<MadarApp> createState() => _MadarAppState();
}

class _MadarAppState extends State<MadarApp> {
  late final AuthController _authController;
  late final FrappeApiClient _apiClient;
  int _unreadNotifications = 0;

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
          _refreshUnreadNotifications();
          return DashboardScreen(
            context: currentContext,
            unreadNotifications: _unreadNotifications,
            onOpenNotifications: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => NotificationScreen(
                    apiClient: _apiClient,
                    onOpenNotification: (notification) =>
                        _openNotificationTarget(context, currentContext, notification),
                  ),
                ),
              );
              _refreshUnreadNotifications();
            },
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
                  builder: (_) => ErpSyncReviewScreen(
                    apiClient: _apiClient,
                    permissions: currentContext.permissions,
                  ),
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
            onOpenMyDeliveryBatches: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) =>
                      DeliveryBatchListScreen(apiClient: _apiClient),
                ),
              );
            },
            onOpenCashbox: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => CashboxScreen(
                    apiClient: _apiClient,
                    userContext: currentContext,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _refreshUnreadNotifications() async {
    if (_authController.context == null) return;
    try {
      final count = await _apiClient.getUnreadNotificationCount();
      if (mounted && count.unreadCount != _unreadNotifications) {
        setState(() => _unreadNotifications = count.unreadCount);
      }
    } catch (_) {
      // Notification count is non-critical for the dashboard.
    }
  }

  Future<bool> _openNotificationTarget(
    BuildContext context,
    UserContext currentContext,
    MadarNotification notification,
  ) async {
    try {
      switch (notification.routeKey) {
        case 'order_detail':
          final orderName = notification.routeParams['order_name'] ?? '';
          if (orderName.isEmpty) return false;
          final order = await _apiClient.getOrder(orderName);
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => OrderDetailScreen(
                apiClient: _apiClient,
                initialOrder: order,
                canCollectPayments: currentContext.permissions.contains(
                  'payments.collect',
                ),
              ),
            ),
          );
          return true;
        case 'approval_queue':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => ApprovalQueueScreen(apiClient: _apiClient),
            ),
          );
          return true;
        case 'production_queue':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => WorkOrderListScreen(apiClient: _apiClient),
            ),
          );
          return true;
        case 'work_order_detail':
          final workOrderName = notification.routeParams['work_order'] ?? '';
          if (workOrderName.isEmpty) return false;
          final workOrder = await _apiClient.getWorkOrder(workOrderName);
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => WorkOrderDetailScreen(
                apiClient: _apiClient,
                initialOrder: workOrder,
              ),
            ),
          );
          return true;
        case 'delivery_batch_detail':
          final batchName = notification.routeParams['batch_name'] ?? '';
          if (batchName.isEmpty) return false;
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => DeliveryBatchDetailScreen(
                apiClient: _apiClient,
                batchName: batchName,
              ),
            ),
          );
          return true;
        case 'my_delivery_batches':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => DeliveryBatchListScreen(apiClient: _apiClient),
            ),
          );
          return true;
        case 'cashbox_detail':
        case 'cashbox_review':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => CashboxScreen(
                apiClient: _apiClient,
                userContext: currentContext,
              ),
            ),
          );
          return true;
        case 'accounting_review_order':
        case 'erp_sync_review':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => ErpSyncReviewScreen(
                apiClient: _apiClient,
                permissions: currentContext.permissions,
              ),
            ),
          );
          return true;
        case 'attendance':
          if (!context.mounted) return false;
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => AttendanceScreen(apiClient: _apiClient),
            ),
          );
          return true;
        default:
          return false;
      }
    } catch (_) {
      return false;
    }
  }
}
