import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'exceptions.dart';

/// Builds the singleton Dio client used to talk to the dashboard backend.
class ApiClient {
  ApiClient._();

  static Dio? _instance;

  static Dio get instance {
    _instance ??= _build();
    return _instance!;
  }

  static Dio _build() {
    final baseUrl = dotenv.maybeGet('BACKEND_URL') ?? 'http://localhost:8080';
    final apiKey = dotenv.maybeGet('DASHBOARD_API_KEY') ?? '';

    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
        responseType: ResponseType.json,
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (apiKey.isNotEmpty) {
            options.headers['X-API-Key'] = apiKey;
          }
          handler.next(options);
        },
        onError: (e, handler) {
          if (e.response?.statusCode == 401) {
            handler.reject(
              DioException(
                requestOptions: e.requestOptions,
                error: UnauthorizedException(
                  'Invalid or missing API key',
                ),
                response: e.response,
              ),
            );
            return;
          }
          handler.next(e);
        },
      ),
    );

    return dio;
  }
}
