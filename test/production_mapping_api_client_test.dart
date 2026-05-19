import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/production/production_mapping_models.dart';

void main() {
  test('production mapping models parse safe envelopes', () {
    final mappings = ProductionMappingList.fromEnvelope({
      'ok': true,
      'data': {
        'items': [
          {
            'name': 'MILK-001',
            'item_code': 'MILK-001',
            'item_name': 'Milk',
            'production_center': 'MAIN',
            'production_department': 'MILK',
            'is_active': 1,
          },
        ],
      },
      'error': null,
    });

    expect(mappings.items.single.itemCode, 'MILK-001');
    expect(mappings.items.single.productionDepartment, 'MILK');
  });

  test('production mapping methods call only Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_production_centers')) {
          return _jsonResponse({
            'message': _listEnvelope([_centerMap()]),
          });
        }
        if (request.url.path.endsWith('list_production_departments')) {
          return _jsonResponse({
            'message': _listEnvelope([_departmentMap()]),
          });
        }
        if (request.url.path.endsWith('list_item_department_mappings')) {
          return _jsonResponse({
            'message': _listEnvelope([_mappingMap()]),
          });
        }
        if (request.url.path.endsWith('validate_order_department_mappings')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'order_name': 'MADAR-ORD-1',
                'is_valid': true,
                'missing_item_codes': [],
                'mapped_item_codes': ['MILK-001'],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {'ok': true, 'data': _mappingMap(), 'error': null},
        });
      }),
    );

    await client.listProductionCenters();
    await client.listProductionDepartments(productionCenter: 'MAIN');
    await client.listItemDepartmentMappings();
    await client.createOrUpdateProductionCenter(
      centerName: 'Main',
      centerCode: 'MAIN',
    );
    await client.createOrUpdateProductionDepartment(
      departmentName: 'Milk',
      departmentCode: 'MILK',
      productionCenter: 'MAIN',
    );
    await client.createOrUpdateItemDepartmentMapping(
      itemCode: 'MILK-001',
      productionCenter: 'MAIN',
      productionDepartment: 'MILK',
    );
    await client.validateOrderDepartmentMappings('MADAR-ORD-1');

    expect(
      requests[0].url.path,
      '/api/method/madar.api.production_mapping.list_production_centers',
    );
    expect(
      requests[1].url.path,
      '/api/method/madar.api.production_mapping.list_production_departments',
    );
    expect(requests[1].url.queryParameters['production_center'], 'MAIN');
    expect(
      requests[2].url.path,
      '/api/method/madar.api.production_mapping.list_item_department_mappings',
    );
    expect(
      requests[3].url.path,
      '/api/method/madar.api.production_mapping.create_or_update_production_center',
    );
    expect(
      requests[4].url.path,
      '/api/method/madar.api.production_mapping.create_or_update_production_department',
    );
    expect(
      requests[5].url.path,
      '/api/method/madar.api.production_mapping.create_or_update_item_department_mapping',
    );
    expect(
      requests[6].url.path,
      '/api/method/madar.api.production_mapping.validate_order_department_mappings',
    );
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _listEnvelope(List<Map<String, dynamic>> items) {
  return {
    'ok': true,
    'data': {'items': items},
    'error': null,
  };
}

Map<String, dynamic> _centerMap() {
  return {
    'name': 'MAIN',
    'center_name': 'Main',
    'center_code': 'MAIN',
    'is_active': 1,
  };
}

Map<String, dynamic> _departmentMap() {
  return {
    'name': 'MILK',
    'department_name': 'Milk',
    'department_code': 'MILK',
    'production_center': 'MAIN',
    'is_active': 1,
  };
}

Map<String, dynamic> _mappingMap() {
  return {
    'name': 'MILK-001',
    'item_code': 'MILK-001',
    'item_name': 'Milk',
    'production_center': 'MAIN',
    'production_department': 'MILK',
    'is_active': 1,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
