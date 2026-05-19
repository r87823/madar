enum AttendanceState {
  inWork,
  outOfWork,
  unknown;

  String get arabicLabel {
    return switch (this) {
      AttendanceState.inWork => 'داخل الدوام',
      AttendanceState.outOfWork => 'خارج الدوام',
      AttendanceState.unknown => 'غير معروف',
    };
  }
}

class AttendanceStatus {
  const AttendanceStatus({
    required this.employeeName,
    required this.state,
    this.employeeId,
    this.lastTime,
    this.lastLogType,
  });

  factory AttendanceStatus.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _asMap(envelope['data']);
    final employee = _asMap(data['employee']);
    final lastCheckin = _asMap(data['last_checkin']);
    return AttendanceStatus(
      employeeId: _nullableString(employee['name']),
      employeeName:
          _nullableString(employee['employee_name']) ??
          _nullableString(employee['name']) ??
          '',
      state: _stateFromCode(_nullableString(data['state'])),
      lastTime: _nullableString(lastCheckin['time']),
      lastLogType: _nullableString(lastCheckin['log_type']),
    );
  }

  final String? employeeId;
  final String employeeName;
  final AttendanceState state;
  final String? lastTime;
  final String? lastLogType;
}

class AttendanceHistory {
  const AttendanceHistory({required this.items});

  factory AttendanceHistory.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _asMap(envelope['data']);
    final rawItems = data['items'];
    final items = rawItems is Iterable
        ? rawItems
              .map((item) => AttendanceHistoryItem.fromJson(_asMap(item)))
              .toList()
        : <AttendanceHistoryItem>[];
    return AttendanceHistory(items: items);
  }

  final List<AttendanceHistoryItem> items;
}

class AttendanceHistoryItem {
  const AttendanceHistoryItem({
    required this.logType,
    required this.time,
    required this.state,
  });

  factory AttendanceHistoryItem.fromJson(Map<String, dynamic> json) {
    return AttendanceHistoryItem(
      logType: _nullableString(json['log_type']) ?? '',
      time: _nullableString(json['time']) ?? '',
      state: _stateFromCode(_nullableString(json['state'])),
    );
  }

  final String logType;
  final String time;
  final AttendanceState state;

  String get arabicLogType {
    return switch (logType) {
      'IN' => 'حضور',
      'OUT' => 'انصراف',
      _ => 'غير معروف',
    };
  }
}

AttendanceState _stateFromCode(String? state) {
  return switch (state) {
    'in_work' => AttendanceState.inWork,
    'out_of_work' => AttendanceState.outOfWork,
    _ => AttendanceState.unknown,
  };
}

Map<String, dynamic> _asMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return value.map((key, value) => MapEntry('$key', value));
  return <String, dynamic>{};
}

String? _nullableString(Object? value) {
  if (value == null) return null;
  final stringValue = '$value';
  return stringValue.isEmpty ? null : stringValue;
}
