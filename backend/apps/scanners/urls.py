from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'scanners'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'agents', views.AgentViewSet)
router.register(r'scanners', views.ActiveScannerViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'scanner-location-mappings', views.ScannerLocationMappingViewSet)

urlpatterns = [
    # AI Agent Builder endpoints (must be before router to avoid slug collision)
    path('agents/generate-prompt/', views.generate_agent_prompt, name='generate-agent-prompt'),
    path('agents/refine-prompt/', views.refine_agent_prompt, name='refine-agent-prompt'),
    path('agents/<slug:slug>/suggest-queries/', views.suggest_agent_queries, name='suggest-agent-queries'),
    path('agents/<slug:slug>/analyze-url/', views.analyze_listing_url, name='analyze-listing-url'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Scanner control endpoints
    path('scanner/start/', views.start_scanner, name='start-scanner'),
    path('scanner/stop/', views.stop_scanner, name='stop-scanner'),
    path('scanner/status/', views.scanner_status, name='scanner-status'),
    path('scanner/single-run/', views.run_single_scan, name='single-scan'),
    path('scanner/history/', views.scan_history, name='scan-history'),
    
    path('scan-batches-debug/', views.scan_batches_debug, name='scan-batches-debug'),
    path('scan-batches/', views.scan_batches_list, name='scan-batches-list'),
    path('scan-batches/<str:scan_id>/', views.scan_batch_detail, name='scan-batch-detail'),
    path('scan-batches/<str:scan_id>/listings/', views.scan_batch_listings, name='scan-batch-listings'),
    path('scan-batches/<str:scan_id>/analyze/', views.run_detailed_analysis, name='run-detailed-analysis'),
    path('scan-batches/<str:scan_id>/reset-analysis/', views.reset_analysis_status, name='reset-analysis-status'),
    
    # AI Usage Tracking endpoints
    path('usage/', views.usage_overview, name='usage-overview'),
    path('usage/<str:scan_id>/', views.scan_usage, name='scan-usage'),
    path('scanners/<int:pk>/agent/', views.scanner_agent_info, name='scanner-agent-info'),
    
    # Manual analysis control endpoints
    path('listings/toggle-investigation/', views.toggle_investigation_status, name='toggle-investigation'),
    path('listings/deep-analysis/', views.run_deep_analysis, name='run-deep-analysis'),
    path('scan-batches/<str:scan_id>/rerun-triage/', views.rerun_triage, name='rerun-triage'),
    path('scan-batches/<str:scan_id>/send-notifications/', views.send_scan_notifications, name='send-scan-notifications'),
    
    # Task status endpoints (for global task indicator)
    path('task/current/', views.get_current_task, name='current-task'),
    path('task/history/', views.get_task_history, name='task-history'),
    path('task/clear/', views.clear_stuck_tasks, name='clear-stuck-tasks'),
    
    # Scanner settings endpoints (auto/manual mode)
    path('settings/', views.get_scanner_settings, name='scanner-settings'),
    path('settings/update/', views.update_scanner_settings, name='update-scanner-settings'),
    path('settings/mode/', views.set_scanner_mode, name='set-scanner-mode'),
    path('settings/auto/enable/', views.enable_auto_scan, name='enable-auto-scan'),
    path('settings/auto/disable/', views.disable_auto_scan, name='disable-auto-scan'),
    
    # Manual scan (controlled version with task tracking)
    path('manual-scan/', views.run_manual_scan, name='manual-scan'),
]
