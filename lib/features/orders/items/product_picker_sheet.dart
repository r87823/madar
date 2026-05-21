import 'package:flutter/material.dart';

import '../../../core/api/frappe_api_client.dart';
import '../../../core/errors/madar_error_messages.dart';
import 'product_models.dart';

class ProductPickerSheet extends StatefulWidget {
  const ProductPickerSheet({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ProductPickerSheet> createState() => _ProductPickerSheetState();
}

class _ProductPickerSheetState extends State<ProductPickerSheet> {
  final _search = TextEditingController();
  ProductList _products = const ProductList(items: []);
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _search,
              decoration: InputDecoration(
                labelText: 'بحث عن منتج',
                suffixIcon: IconButton(
                  tooltip: 'بحث',
                  onPressed: _load,
                  icon: const Icon(Icons.search),
                ),
              ),
              onSubmitted: (_) => _load(),
            ),
            const SizedBox(height: 12),
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(20),
                child: CircularProgressIndicator(),
              )
            else if (_error != null)
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              )
            else
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: _products.items
                      .map(
                        (product) => ListTile(
                          title: Text(product.itemName),
                          subtitle: Text(
                            '${product.itemCode} - ${product.defaultPrice.toStringAsFixed(2)}',
                          ),
                          onTap: () => Navigator.of(context).pop(product),
                        ),
                      )
                      .toList(growable: false),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final products = await widget.apiClient.listProducts(
        search: _search.text.trim(),
      );
      setState(() {
        _products = products;
      });
    } catch (error) {
      setState(() {
        _error = arabicMessageForError(error);
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
}
