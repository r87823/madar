class UserContext {
  const UserContext({
    required this.user,
    required this.fullName,
    required this.roles,
    required this.permissions,
    required this.scopes,
    this.employee,
    this.branch,
  });

  factory UserContext.fromFrappeMessage(Map<String, dynamic> payload) {
    final message = _asMap(payload['message'] ?? payload);
    return UserContext(
      user: _asString(message['user']),
      fullName: _asString(message['full_name']),
      roles: _asStringList(message['roles']),
      permissions: _asStringList(message['permissions']),
      employee: EmployeeContext.fromJsonOrNull(message['employee']),
      branch: BranchContext.fromJsonOrNull(message['branch']),
      scopes: ScopeContext.fromJson(_asMap(message['scopes'])),
    );
  }

  final String user;
  final String fullName;
  final List<String> roles;
  final List<String> permissions;
  final EmployeeContext? employee;
  final BranchContext? branch;
  final ScopeContext scopes;
}

class EmployeeContext {
  const EmployeeContext({
    required this.name,
    required this.employeeName,
    this.company,
    this.department,
    this.designation,
    this.branch,
    this.image,
    this.status,
  });

  factory EmployeeContext.fromJson(Map<String, dynamic> json) {
    return EmployeeContext(
      name: _asString(json['name']),
      employeeName: _asString(json['employee_name']),
      company: _nullableString(json['company']),
      department: _nullableString(json['department']),
      designation: _nullableString(json['designation']),
      branch: _nullableString(json['branch']),
      image: _nullableString(json['image']),
      status: _nullableString(json['status']),
    );
  }

  static EmployeeContext? fromJsonOrNull(Object? value) {
    if (value == null) return null;
    final map = _asMap(value);
    if (map.isEmpty) return null;
    return EmployeeContext.fromJson(map);
  }

  final String name;
  final String employeeName;
  final String? company;
  final String? department;
  final String? designation;
  final String? branch;
  final String? image;
  final String? status;

  Map<String, String> toDisplayRows() {
    return {
      'رقم الموظف': name,
      'اسم الموظف': employeeName,
      if (company != null && company!.isNotEmpty) 'الشركة': company!,
      if (department != null && department!.isNotEmpty) 'القسم': department!,
      if (designation != null && designation!.isNotEmpty)
        'المسمى': designation!,
      if (branch != null && branch!.isNotEmpty) 'الفرع': branch!,
      if (status != null && status!.isNotEmpty) 'الحالة': status!,
    };
  }
}

class BranchContext {
  const BranchContext({required this.name, this.branch, this.company});

  factory BranchContext.fromJson(Map<String, dynamic> json) {
    return BranchContext(
      name: _asString(json['name']),
      branch: _nullableString(json['branch']),
      company: _nullableString(json['company']),
    );
  }

  static BranchContext? fromJsonOrNull(Object? value) {
    if (value == null) return null;
    final map = _asMap(value);
    if (map.isEmpty) return null;
    return BranchContext.fromJson(map);
  }

  final String name;
  final String? branch;
  final String? company;
}

class ScopeContext {
  const ScopeContext({
    required this.branchNames,
    required this.departmentNames,
  });

  factory ScopeContext.fromJson(Map<String, dynamic> json) {
    return ScopeContext(
      branchNames: _asStringList(json['branch_names']),
      departmentNames: _asStringList(json['department_names']),
    );
  }

  final List<String> branchNames;
  final List<String> departmentNames;
}

Map<String, dynamic> _asMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return value.map((key, value) => MapEntry('$key', value));
  return <String, dynamic>{};
}

List<String> _asStringList(Object? value) {
  if (value is Iterable) {
    return value
        .map((item) => '$item')
        .where((item) => item.isNotEmpty)
        .toList();
  }
  return const [];
}

String _asString(Object? value) => value == null ? '' : '$value';

String? _nullableString(Object? value) {
  if (value == null) return null;
  final stringValue = '$value';
  return stringValue.isEmpty ? null : stringValue;
}
