import logging
from typing import Dict, Optional
from django.conf import settings
from mixpanel import Mixpanel
from django.http import HttpRequest
from user_agents import parse
import time

logger = logging.getLogger(__name__)

class MixpanelService:
    """Service class for Mixpanel event tracking"""
    
    def __init__(self):
        self.mp = Mixpanel(settings.MIXPANEL_PROJECT_TOKEN)
        self.enabled = settings.MIXPANEL_ENABLED

    def _get_user_metadata(self, request: Optional[HttpRequest] = None) -> Dict:
        """Extract common user metadata from request"""
        metadata = {}
        
        if request:
            # Parse user agent
            user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
            metadata.update({
                'browser': user_agent.browser.family,
                'browser_version': user_agent.browser.version_string,
                'os': user_agent.os.family,
                'device': user_agent.device.family,
                'referrer': request.META.get('HTTP_REFERER'),
            })
            
            # Get UTM parameters
            utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
            for param in utm_params:
                value = request.GET.get(param)
                if value:
                    metadata[param] = value
        
        return metadata

    def track(self, distinct_id: str, event_name: str, properties: Dict = None, request: HttpRequest = None):
        """Track an event in Mixpanel"""
        if not self.enabled:
            return
        
        try:
            # Combine custom properties with common metadata
            event_properties = {
                'timestamp': int(time.time()),
                **self._get_user_metadata(request),
                **(properties or {})
            }
            
            self.mp.track(distinct_id, event_name.title(), event_properties)
        except Exception as e:
            logger.error(f"Error tracking Mixpanel event {event_name}: {str(e)}")
    
    def people_set(self, distinct_id: str, properties: Dict = None):
        """Set properties for a user in Mixpanel People"""
        if not self.enabled:
            return
        
        try:
            # Combine provided properties with common metadata
            user_properties = {
                **(properties or {})
            }
            
            self.mp.people_set(distinct_id, user_properties)
        except Exception as e:
            logger.error(f"Error setting Mixpanel People properties for user {distinct_id}: {str(e)}")