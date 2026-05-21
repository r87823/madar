import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import 'followup_dashboard_models.dart';

class FollowupDashboardScreen extends StatefulWidget {
  const FollowupDashboardScreen({
    required this.apiClient,
    this.onOpenRoute,
    super.key,
  });

  final FrappeApiClient apiClient;
  final Future<bool> Function(String routeKey, Map<String, String> routeParams)?
  onOpenRoute;

  @override
  State<FollowupDashboardScreen> createState() =>
      _FollowupDashboardScreenState();
}

class _FollowupDashboardScreenState extends State<FollowupDashboardScreen> {
  late Future<FollowupDashboardSummary> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getFollowupDashboardSummary();
  }

  Future<void> _reload() async {
    setState(() {
      _future = widget.apiClient.getFollowupDashboardSummary();
    });
    await _future;
  }

  Future<void> _open(String routeKey, Map<String, String> routeParams) async {
    if (routeKey == 'none') {
      _showUnsupported();
      return;
    }
    final opened =
        await (widget.onOpenRoute?.call(routeKey, routeParams) ??
            Future.value(false));
    if (!mounted) return;
    if (!opened) _showUnsupported();
  }

  void _showUnsupported() {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('لا يمكن فتح هذا القسم الآن')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('لوحة المتابعة')),
      body: FutureBuilder<FollowupDashboardSummary>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _StateMessage(
              message: arabicMessageForError(snapshot.error),
              onRetry: _reload,
            );
          }
          final summary =
              snapshot.data ??
              const FollowupDashboardSummary(cards: [], alerts: []);
          if (summary.cards.isEmpty && summary.alerts.isEmpty) {
            return const _StateMessage(message: 'لا توجد بيانات للعرض');
          }
          return RefreshIndicator(
            onRefresh: _reload,
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (summary.alerts.isNotEmpty) ...[
                  Text(
                    'تنبيهات',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ...summary.alerts.map(
                    (alert) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _AlertCard(
                        alert: alert,
                        onTap: () => _open(alert.routeKey, alert.routeParams),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = constraints.maxWidth;
                    final count = width >= 900
                        ? 3
                        : width >= 620
                        ? 2
                        : 1;
                    return GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: summary.cards.length,
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: count,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                        childAspectRatio: width < 520 ? 1.75 : 1.55,
                      ),
                      itemBuilder: (context, index) {
                        final card = summary.cards[index];
                        return _SummaryCard(
                          card: card,
                          onTap: () => _open(card.routeKey, card.routeParams),
                        );
                      },
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.card, required this.onTap});

  final FollowupDashboardCard card;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: card.isHighPriority ? colorScheme.errorContainer : Colors.white,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                card.title,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const Spacer(),
              Text(
                card.valueText,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(card.subtitle),
            ],
          ),
        ),
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  const _AlertCard({required this.alert, required this.onTap});

  final FollowupDashboardAlert alert;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: alert.priority == 'high'
          ? colorScheme.errorContainer
          : colorScheme.secondaryContainer,
      child: ListTile(
        onTap: onTap,
        title: Text(alert.title),
        subtitle: Text(alert.message),
        leading: const Icon(Icons.warning_amber_outlined),
      ),
    );
  }
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.message, this.onRetry});

  final String message;
  final Future<void> Function()? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('إعادة المحاولة'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
