enum CashboxStatus {
  open,
  submitted,
  approved,
  returned,
  closed,
  unknown;

  String get arabicLabel {
    switch (this) {
      case CashboxStatus.open:
        return 'مفتوح';
      case CashboxStatus.submitted:
        return 'مرسل للمراجعة';
      case CashboxStatus.approved:
        return 'معتمد';
      case CashboxStatus.returned:
        return 'معاد للتعديل';
      case CashboxStatus.closed:
        return 'مغلق';
      case CashboxStatus.unknown:
        return 'غير معروف';
    }
  }

  static CashboxStatus fromString(String? value) {
    switch (value) {
      case 'open':
        return CashboxStatus.open;
      case 'submitted':
        return CashboxStatus.submitted;
      case 'approved':
        return CashboxStatus.approved;
      case 'returned':
        return CashboxStatus.returned;
      case 'closed':
        return CashboxStatus.closed;
      default:
        return CashboxStatus.unknown;
    }
  }
}

class Cashbox {
  const Cashbox({
    required this.name,
    required this.user,
    required this.cashboxDate,
    required this.status,
    required this.expectedCash,
    required this.submittedCash,
    required this.difference,
    required this.entries,
    this.submittedAt,
    this.reviewedBy,
    this.reviewedAt,
    this.returnReason,
  });

  final String name;
  final String user;
  final String cashboxDate;
  final CashboxStatus status;
  final double expectedCash;
  final double submittedCash;
  final double difference;
  final List<CashboxEntry> entries;
  final String? submittedAt;
  final String? reviewedBy;
  final String? reviewedAt;
  final String? returnReason;

  factory Cashbox.fromMap(Map<String, dynamic> map) {
    final rawEntries = map['entries'];
    return Cashbox(
      name: map['name']?.toString() ?? '',
      user: map['user']?.toString() ?? '',
      cashboxDate: map['cashbox_date']?.toString() ?? '',
      status: CashboxStatus.fromString(map['status']?.toString()),
      expectedCash: _toDouble(map['expected_cash']),
      submittedCash: _toDouble(map['submitted_cash']),
      difference: _toDouble(map['difference']),
      submittedAt: map['submitted_at']?.toString(),
      reviewedBy: map['reviewed_by']?.toString(),
      reviewedAt: map['reviewed_at']?.toString(),
      returnReason: map['return_reason']?.toString(),
      entries: rawEntries is List
          ? rawEntries
                .whereType<Map>()
                .map(
                  (item) => item.map((key, value) => MapEntry('$key', value)),
                )
                .map(CashboxEntry.fromMap)
                .toList(growable: false)
          : const [],
    );
  }

  factory Cashbox.fromEnvelope(Map<String, dynamic> envelope) {
    return Cashbox.fromMap(_dataMap(envelope));
  }
}

class CashboxEntry {
  const CashboxEntry({
    required this.name,
    required this.cashbox,
    required this.payment,
    required this.madarOrder,
    required this.amount,
    required this.entryType,
    this.createdByUser,
    this.createdAt,
  });

  final String name;
  final String cashbox;
  final String payment;
  final String madarOrder;
  final double amount;
  final String entryType;
  final String? createdByUser;
  final String? createdAt;

  factory CashboxEntry.fromMap(Map<String, dynamic> map) {
    return CashboxEntry(
      name: map['name']?.toString() ?? '',
      cashbox: map['cashbox']?.toString() ?? '',
      payment: map['payment']?.toString() ?? '',
      madarOrder: map['madar_order']?.toString() ?? '',
      amount: _toDouble(map['amount']),
      entryType: map['entry_type']?.toString() ?? '',
      createdByUser: map['created_by_user']?.toString(),
      createdAt: map['created_at']?.toString(),
    );
  }
}

class CashboxEntryList {
  const CashboxEntryList({required this.items});

  final List<CashboxEntry> items;

  factory CashboxEntryList.fromEnvelope(Map<String, dynamic> envelope) {
    final rawItems = _dataMap(envelope)['items'];
    return CashboxEntryList(
      items: rawItems is List
          ? rawItems
                .whereType<Map>()
                .map(
                  (item) => item.map((key, value) => MapEntry('$key', value)),
                )
                .map(CashboxEntry.fromMap)
                .toList(growable: false)
          : const [],
    );
  }
}

class CashboxList {
  const CashboxList({required this.items});

  final List<Cashbox> items;

  factory CashboxList.fromEnvelope(Map<String, dynamic> envelope) {
    final rawItems = _dataMap(envelope)['items'];
    return CashboxList(
      items: rawItems is List
          ? rawItems
                .whereType<Map>()
                .map(
                  (item) => item.map((key, value) => MapEntry('$key', value)),
                )
                .map(Cashbox.fromMap)
                .toList(growable: false)
          : const [],
    );
  }
}

Map<String, dynamic> _dataMap(Map<String, dynamic> envelope) {
  final data = envelope['data'];
  return data is Map
      ? data.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
