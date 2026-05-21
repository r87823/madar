import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import '../orders/items/product_models.dart';
import 'production_mapping_models.dart';

class ProductionMappingScreen extends StatefulWidget {
  const ProductionMappingScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ProductionMappingScreen> createState() =>
      _ProductionMappingScreenState();
}

class _ProductionMappingScreenState extends State<ProductionMappingScreen> {
  final _centerNameController = TextEditingController(
    text: 'Main Production Center',
  );
  final _centerCodeController = TextEditingController(text: 'MAIN');
  final _departmentNameController = TextEditingController(
    text: 'Milk Department',
  );
  final _departmentCodeController = TextEditingController(text: 'MILK');

  List<ProductItem> _products = const [];
  List<ProductionCenter> _centers = const [];
  List<ProductionDepartment> _departments = const [];
  List<ProductionMapping> _mappings = const [];
  String? _selectedItemCode;
  String? _selectedCenter;
  String? _selectedDepartment;
  bool _isLoading = true;
  bool _isSaving = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _centerNameController.dispose();
    _centerCodeController.dispose();
    _departmentNameController.dispose();
    _departmentCodeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('إعدادات الإنتاج')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  _message!,
                  style: TextStyle(
                    color: _isError
                        ? Theme.of(context).colorScheme.error
                        : Theme.of(context).colorScheme.primary,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else ...[
              _MasterDataCard(
                centerNameController: _centerNameController,
                centerCodeController: _centerCodeController,
                departmentNameController: _departmentNameController,
                departmentCodeController: _departmentCodeController,
                selectedCenter: _selectedCenter,
                centers: _centers,
                isSaving: _isSaving,
                onCenterChanged: (value) =>
                    setState(() => _selectedCenter = value),
                onSaveCenter: _saveCenter,
                onSaveDepartment: _saveDepartment,
              ),
              const SizedBox(height: 12),
              _MappingEditorCard(
                products: _products,
                centers: _centers,
                departments: _visibleDepartments,
                selectedItemCode: _selectedItemCode,
                selectedCenter: _selectedCenter,
                selectedDepartment: _selectedDepartment,
                isSaving: _isSaving,
                onItemChanged: (value) =>
                    setState(() => _selectedItemCode = value),
                onCenterChanged: (value) {
                  setState(() {
                    _selectedCenter = value;
                    _selectedDepartment = _firstDepartmentFor(value);
                  });
                },
                onDepartmentChanged: (value) =>
                    setState(() => _selectedDepartment = value),
                onSave: _saveMapping,
              ),
              const SizedBox(height: 12),
              _MappingsList(mappings: _mappings),
            ],
          ],
        ),
      ),
    );
  }

  List<ProductionDepartment> get _visibleDepartments {
    if (_selectedCenter == null || _selectedCenter!.isEmpty) {
      return _departments;
    }
    return _departments
        .where((department) => department.productionCenter == _selectedCenter)
        .toList(growable: false);
  }

  Future<void> _load({bool preserveMessage = false}) async {
    setState(() {
      _isLoading = true;
      if (!preserveMessage) {
        _message = null;
        _isError = false;
      }
    });
    try {
      final results = await Future.wait([
        widget.apiClient.listProducts(),
        widget.apiClient.listProductionCenters(),
        widget.apiClient.listProductionDepartments(),
        widget.apiClient.listItemDepartmentMappings(),
      ]);
      if (!mounted) return;
      final products = results[0] as ProductList;
      final centers = results[1] as ProductionCenterList;
      final departments = results[2] as ProductionDepartmentList;
      final mappings = results[3] as ProductionMappingList;
      setState(() {
        _products = products.items;
        _centers = centers.items;
        _departments = departments.items;
        _mappings = mappings.items;
        _selectedItemCode ??= _products.isEmpty
            ? null
            : _products.first.itemCode;
        _selectedCenter ??= _centers.isEmpty ? null : _centers.first.name;
        _selectedDepartment ??= _firstDepartmentFor(_selectedCenter);
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _saveCenter() async {
    await _saving(() async {
      final center = await widget.apiClient.createOrUpdateProductionCenter(
        centerName: _centerNameController.text,
        centerCode: _centerCodeController.text,
      );
      setState(() {
        _selectedCenter = center.name;
        _message = 'تم حفظ مركز الإنتاج';
      });
      await _load(preserveMessage: true);
    });
  }

  Future<void> _saveDepartment() async {
    final center = _selectedCenter;
    if (center == null || center.isEmpty) {
      setState(() {
        _message = 'اختر مركز الإنتاج أولًا';
        _isError = true;
      });
      return;
    }
    await _saving(() async {
      final department = await widget.apiClient
          .createOrUpdateProductionDepartment(
            departmentName: _departmentNameController.text,
            departmentCode: _departmentCodeController.text,
            productionCenter: center,
          );
      setState(() {
        _selectedDepartment = department.name;
        _message = 'تم حفظ قسم الإنتاج';
      });
      await _load(preserveMessage: true);
    });
  }

  Future<void> _saveMapping() async {
    final itemCode = _selectedItemCode;
    final center = _selectedCenter;
    final department = _selectedDepartment;
    if (itemCode == null || center == null || department == null) {
      setState(() {
        _message = 'اختر المنتج والمركز والقسم';
        _isError = true;
      });
      return;
    }
    await _saving(() async {
      await widget.apiClient.createOrUpdateItemDepartmentMapping(
        itemCode: itemCode,
        productionCenter: center,
        productionDepartment: department,
      );
      setState(() {
        _message = 'تم حفظ الربط';
      });
      await _load(preserveMessage: true);
    });
  }

  Future<void> _saving(Future<void> Function() action) async {
    setState(() {
      _isSaving = true;
      _message = null;
      _isError = false;
    });
    try {
      await action();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  String? _firstDepartmentFor(String? center) {
    final visible = center == null
        ? _departments
        : _departments.where(
            (department) => department.productionCenter == center,
          );
    return visible.isEmpty ? null : visible.first.name;
  }
}

class _MasterDataCard extends StatelessWidget {
  const _MasterDataCard({
    required this.centerNameController,
    required this.centerCodeController,
    required this.departmentNameController,
    required this.departmentCodeController,
    required this.selectedCenter,
    required this.centers,
    required this.isSaving,
    required this.onCenterChanged,
    required this.onSaveCenter,
    required this.onSaveDepartment,
  });

  final TextEditingController centerNameController;
  final TextEditingController centerCodeController;
  final TextEditingController departmentNameController;
  final TextEditingController departmentCodeController;
  final String? selectedCenter;
  final List<ProductionCenter> centers;
  final bool isSaving;
  final ValueChanged<String?> onCenterChanged;
  final VoidCallback onSaveCenter;
  final VoidCallback onSaveDepartment;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'بيانات الإنتاج',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: centerNameController,
              decoration: const InputDecoration(labelText: 'اسم مركز الإنتاج'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: centerCodeController,
              decoration: const InputDecoration(labelText: 'رمز المركز'),
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: isSaving ? null : onSaveCenter,
              icon: const Icon(Icons.save_outlined),
              label: const Text('حفظ مركز الإنتاج'),
            ),
            const Divider(height: 28),
            DropdownButtonFormField<String>(
              initialValue: selectedCenter,
              decoration: const InputDecoration(labelText: 'مركز القسم'),
              items: centers
                  .map(
                    (center) => DropdownMenuItem(
                      value: center.name,
                      child: Text(center.centerName),
                    ),
                  )
                  .toList(growable: false),
              onChanged: onCenterChanged,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: departmentNameController,
              decoration: const InputDecoration(labelText: 'اسم قسم الإنتاج'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: departmentCodeController,
              decoration: const InputDecoration(labelText: 'رمز القسم'),
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: isSaving ? null : onSaveDepartment,
              icon: const Icon(Icons.save_outlined),
              label: const Text('حفظ قسم الإنتاج'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MappingEditorCard extends StatelessWidget {
  const _MappingEditorCard({
    required this.products,
    required this.centers,
    required this.departments,
    required this.selectedItemCode,
    required this.selectedCenter,
    required this.selectedDepartment,
    required this.isSaving,
    required this.onItemChanged,
    required this.onCenterChanged,
    required this.onDepartmentChanged,
    required this.onSave,
  });

  final List<ProductItem> products;
  final List<ProductionCenter> centers;
  final List<ProductionDepartment> departments;
  final String? selectedItemCode;
  final String? selectedCenter;
  final String? selectedDepartment;
  final bool isSaving;
  final ValueChanged<String?> onItemChanged;
  final ValueChanged<String?> onCenterChanged;
  final ValueChanged<String?> onDepartmentChanged;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'ربط الأصناف بالأقسام',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: selectedItemCode,
              decoration: const InputDecoration(labelText: 'المنتج'),
              items: products
                  .map(
                    (product) => DropdownMenuItem(
                      value: product.itemCode,
                      child: Text(product.itemName),
                    ),
                  )
                  .toList(growable: false),
              onChanged: onItemChanged,
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: selectedCenter,
              decoration: const InputDecoration(labelText: 'مركز الإنتاج'),
              items: centers
                  .map(
                    (center) => DropdownMenuItem(
                      value: center.name,
                      child: Text(center.centerName),
                    ),
                  )
                  .toList(growable: false),
              onChanged: onCenterChanged,
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: selectedDepartment,
              decoration: const InputDecoration(labelText: 'قسم الإنتاج'),
              items: departments
                  .map(
                    (department) => DropdownMenuItem(
                      value: department.name,
                      child: Text(department.departmentName),
                    ),
                  )
                  .toList(growable: false),
              onChanged: onDepartmentChanged,
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: isSaving ? null : onSave,
              icon: const Icon(Icons.link_outlined),
              label: const Text('حفظ الربط'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MappingsList extends StatelessWidget {
  const _MappingsList({required this.mappings});

  final List<ProductionMapping> mappings;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'الربط الحالي',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            if (mappings.isEmpty)
              Text(
                'لا يوجد ربط أصناف بعد.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...mappings.map(
                (mapping) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    mapping.itemName.isEmpty
                        ? mapping.itemCode
                        : mapping.itemName,
                  ),
                  subtitle: Text(
                    '${mapping.productionCenter} / ${mapping.productionDepartment}',
                  ),
                  trailing: mapping.isActive
                      ? const Text('نشط')
                      : const Text('غير نشط'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
