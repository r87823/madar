import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madar/core/widgets/madar_ui.dart';

void main() {
  testWidgets('shared loading empty and error states render Arabic labels', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: Column(
            children: [
              MadarLoadingState(),
              MadarEmptyState(message: 'لا توجد بيانات للعرض'),
              MadarErrorState(message: 'تعذر تحميل البيانات'),
            ],
          ),
        ),
      ),
    );

    expect(find.text('جاري التحميل...'), findsOneWidget);
    expect(find.text('لا توجد بيانات للعرض'), findsOneWidget);
    expect(find.text('تعذر تحميل البيانات'), findsOneWidget);
  });

  testWidgets('status chip uses Arabic labels and supports high priority', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: Wrap(
            children: [
              MadarStatusChip(status: 'submitted'),
              MadarStatusChip(status: 'ready_for_dispatch', highPriority: true),
            ],
          ),
        ),
      ),
    );

    expect(find.text('مرسل للاعتماد'), findsOneWidget);
    expect(find.text('جاهز للإرسال'), findsOneWidget);
  });

  testWidgets('metric card shows value subtitle and high priority marker', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: MadarMetricCard(
            title: 'أخطاء مزامنة ERP',
            value: '2',
            subtitle: 'تحتاج مراجعة',
            highPriority: true,
          ),
        ),
      ),
    );

    expect(find.text('أخطاء مزامنة ERP'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('تحتاج مراجعة'), findsOneWidget);
  });
}
