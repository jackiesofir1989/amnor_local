from datetime import datetime
from typing import List

from fastapi_utils.api_model import APIModel

from devices.event import Event


class Schedule(APIModel):
    events: List[Event]

    def get_current_event(self) -> Event:
        current_time = datetime.now().time()
        last_event: Event = self.events[0]
        for i, event in enumerate(self.events[1:]):
            if last_event.start_time <= current_time < event.start_time:
                return last_event
            last_event = event
        return last_event

    def get_current_input_vector(self) -> List[int]:
        event = self.get_current_event()
        return event.colors

    def get_current_moles_desired(self) -> int:
        event = self.get_current_event()
        return event.moles_desired
