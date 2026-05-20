import 'package:dio/dio.dart';

import '../models/broker.dart';
import '../models/community.dart';
import '../models/event_recommendation.dart';
import '../models/influencer.dart';
import '../models/promo_reach.dart';
import '../models/user_summary.dart';
import 'client.dart';
import 'exceptions.dart';

/// Thin wrapper around the backend HTTP endpoints. Each method maps to one
/// route documented in the dashboard API contract.
class DashboardApi {
  DashboardApi({Dio? dio}) : _dio = dio ?? ApiClient.instance;

  final Dio _dio;

  Future<bool> health() async {
    try {
      final res = await _dio.get('/health');
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<List<UserSummary>> users({int limit = 500}) async {
    final data = await _get('/users', query: {'limit': limit});
    return (data['users'] as List<dynamic>)
        .map((e) => UserSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PromoReach> promoReach(String userId) async {
    final data = await _get('/promo-reach/$userId');
    return PromoReach.fromJson(data);
  }

  Future<InfluencerRanking> influencers({int limit = 10}) async {
    final data = await _get('/influencers', query: {'limit': limit});
    return InfluencerRanking.fromJson(data);
  }

  Future<EventRecommendationList> eventRecommendations(
    String userId, {
    int limit = 10,
  }) async {
    final data = await _get(
      '/event-recommendations/$userId',
      query: {'limit': limit},
    );
    return EventRecommendationList.fromJson(data);
  }

  Future<CommunitiesOverview> communities({int minSize = 2}) async {
    final data = await _get('/communities', query: {'min_size': minSize});
    return CommunitiesOverview.fromJson(data);
  }

  Future<BrokerRanking> brokers({int limit = 10}) async {
    final data = await _get('/brokers', query: {'limit': limit});
    return BrokerRanking.fromJson(data);
  }

  Future<Map<String, dynamic>> _get(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        path,
        queryParameters: query,
      );
      final body = res.data;
      if (body == null) {
        throw ApiException('Empty response from $path');
      }
      return body;
    } on DioException catch (e) {
      if (e.error is ApiException) {
        throw e.error as ApiException;
      }
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout) {
        throw NetworkException(
          'Cannot reach backend (${e.requestOptions.baseUrl})',
        );
      }
      final code = e.response?.statusCode;
      throw ApiException(
        e.message ?? 'Request failed',
        statusCode: code,
      );
    }
  }
}
