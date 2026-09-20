class AgentState:
    def __init__(self):
        self.current_poi = None
        self.visited_pois = []
        self.status = "idle"

    def set_current_poi(self, poi_id: str):
        self.current_poi = poi_id

        if poi_id not in self.visited_pois:
            self.visited_pois.append(poi_id)

    def set_status(self, status: str):
        self.status = status

    def to_dict(self):
        return {
            "current_poi": self.current_poi,
            "visited_pois": self.visited_pois,
            "status": self.status,
        }