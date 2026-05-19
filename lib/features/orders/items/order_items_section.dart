import 'package:flutter/material.dart';

import 'order_item_models.dart';

class OrderItemsSection extends StatelessWidget {
  const OrderItemsSection({
    required this.items,
    required this.subtotal,
    required this.canEdit,
    required this.onAdd,
    required this.onIncrease,
    required this.onDecrease,
    required this.onRemove,
    super.key,
  });

  final List<MadarOrderItem> items;
  final double subtotal;
  final bool canEdit;
  final VoidCallback onAdd;
  final ValueChanged<MadarOrderItem> onIncrease;
  final ValueChanged<MadarOrderItem> onDecrease;
  final ValueChanged<MadarOrderItem> onRemove;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'الأصناف',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                if (canEdit)
                  FilledButton.icon(
                    onPressed: onAdd,
                    icon: const Icon(Icons.add),
                    label: const Text('إضافة صنف'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (items.isEmpty)
              Text(
                'لا توجد أصناف بعد.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...items.map(
                (item) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(item.itemName),
                  subtitle: Text(
                    '${item.qty.toStringAsFixed(2)} × ${item.unitPrice.toStringAsFixed(2)}',
                  ),
                  trailing: canEdit
                      ? Wrap(
                          spacing: 4,
                          children: [
                            IconButton(
                              tooltip: 'زيادة',
                              onPressed: () => onIncrease(item),
                              icon: const Icon(Icons.add),
                            ),
                            IconButton(
                              tooltip: 'تقليل',
                              onPressed: () => onDecrease(item),
                              icon: const Icon(Icons.remove),
                            ),
                            IconButton(
                              tooltip: 'حذف',
                              onPressed: () => onRemove(item),
                              icon: const Icon(Icons.delete_outline),
                            ),
                          ],
                        )
                      : Text(item.lineTotal.toStringAsFixed(2)),
                ),
              ),
            const Divider(height: 24),
            Text(
              'الإجمالي: ${subtotal.toStringAsFixed(2)}',
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ],
        ),
      ),
    );
  }
}
