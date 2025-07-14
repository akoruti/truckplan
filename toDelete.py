import pandas as pd
from datetime import datetime, timedelta

class TripScheduler:
    """
    A class to manage and schedule trips for drivers, calculate costs,
    and select compatible routes based on availability.
    """

    def __init__(self, fuel_consumption_km_per_l=3.5, fuel_price_per_l=1.69, rest_unload_minutes=45, rest_hours=11, toll_rate_per_km=0.2):
        # Initialize empty DataFrame for trips
        self.trips = pd.DataFrame(columns=[
            'Codice Viaggio', 'Partenza', 'DataPartenza', 'Destinazione', 'DataArrivo',
            'Distanza_km', 'Durata_h', 'Compenso_eur', 'Eur_per_km', 'Rimorchio', 'Modalita'
        ])
        # Cost parameters
        self.fuel_consumption = fuel_consumption_km_per_l    # km per liter
        self.fuel_price = fuel_price_per_l                   # eur per liter
        self.toll_rate = toll_rate_per_km                    # eur per km
        # Rest parameters
        self.unload_rest = timedelta(minutes=rest_unload_minutes)
        self.daily_rest = timedelta(hours=rest_hours)

    def add_trip(self, trip_info: dict):
        """
        Add a trip to the schedule. trip_info keys:
        'Codice Viaggio', 'Partenza', 'DataPartenza' (datetime), 'Destinazione', 'DataArrivo' (datetime),
        'Distanza_km', 'Durata_h', 'Compenso_eur', 'Eur_per_km', 'Rimorchio', 'Modalita'
        """
        self.trips = pd.concat([self.trips, pd.DataFrame([trip_info])], ignore_index=True)

    def calculate_fuel_cost(self, distance_km: float) -> float:
        """
        Estimate fuel cost for given distance.
        """
        liters = distance_km / self.fuel_consumption
        return liters * self.fuel_price

    def calculate_toll_cost(self, distance_km: float) -> float:
        """
        Estimate toll cost for given distance.
        """
        return distance_km * self.toll_rate

    def calculate_trip_costs(self):
        """
        Add columns 'FuelCost_eur', 'TollCost_eur', 'TotalCost_eur' to trips DataFrame.
        """
        self.trips['FuelCost_eur'] = self.trips['Distanza_km'].apply(self.calculate_fuel_cost)
        self.trips['TollCost_eur'] = self.trips['Distanza_km'].apply(self.calculate_toll_cost)
        self.trips['TotalCost_eur'] = self.trips['FuelCost_eur'] + self.trips['TollCost_eur']

    def next_available(self) -> datetime:
        """
        Calculate next availability time: last arrival + unload rest + daily rest.
        """
        if self.trips.empty:
            return datetime.now()
        last_arrival = self.trips['DataArrivo'].max()
        return last_arrival + self.unload_rest + self.daily_rest

    def select_compatible_routes(self, routes_df: pd.DataFrame, min_comp: float = None,
                                 min_eur_per_km: float = None, min_km: float = None, top_n: int = 3) -> pd.DataFrame:
        """
        From a DataFrame of candidate routes, filter those starting after next_available,
        apply optional filters (min compensation, min eur/km, min distance),
        sort by compensation and eur/km descending, return top_n.
        routes_df must have columns: 'DataPartenza' (datetime), 'Distanza_km', 'Compenso_eur', 'Eur_per_km'
        """
        avail = self.next_available()
        df = routes_df.copy()
        df = df[df['DataPartenza'] >= avail]
        if min_comp is not None:
            df = df[df['Compenso_eur'] >= min_comp]
        if min_eur_per_km is not None:
            df = df[df['Eur_per_km'] >= min_eur_per_km]
        if min_km is not None:
            df = df[df['Distanza_km'] >= min_km]
        df = df.sort_values(['Compenso_eur', 'Eur_per_km'], ascending=False)
        return df.head(top_n)

    def totals(self) -> dict:
        """
        Return a summary of totals: km, compensation, fuel, tolls, drive hours.
        """
        self.calculate_trip_costs()
        total_km = self.trips['Distanza_km'].sum()
        total_comp = self.trips['Compenso_eur'].sum()
        total_fuel = self.trips['FuelCost_eur'].sum()
        total_toll = self.trips['TollCost_eur'].sum()
        total_hours = self.trips['Durata_h'].sum()
        avg_eur_per_km = total_comp / total_km if total_km else 0
        return {
            'total_km': total_km,
            'total_comp_eur': total_comp,
            'total_fuel_eur': total_fuel,
            'total_toll_eur': total_toll,
            'total_cost_eur': total_fuel + total_toll,
            'total_drive_h': total_hours,
            'avg_eur_per_km': avg_eur_per_km,
            'num_trips': len(self.trips)
        }

    def save_csv(self, filename: str):
        """
        Save the trips DataFrame (including computed costs) to a CSV.
        """
        self.calculate_trip_costs()
        self.trips.to_csv(filename, index=False)


if __name__ == "__main__":
    # Example usage
    scheduler = TripScheduler()
    # Add trips manually (example)
    scheduler.add_trip({
        'Codice Viaggio': '115C6227S',
        'Partenza': 'NUE9 Eggolsheim',
        'DataPartenza': datetime(2025, 7, 10, 8, 30),
        'Destinazione': "LIN8 Casirate D'Adda",
        'DataArrivo': datetime(2025, 7, 11, 14, 15),
        'Distanza_km': 728.0,
        'Durata_h': 9.5,
        'Compenso_eur': 1508.46,
        'Eur_per_km': 2.07,
        'Rimorchio': 'Rimorchio sganciato',
        'Modalita': 'In tempo reale'
    })
    # Display totals
    print(scheduler.totals())
    # Suppose you have a DataFrame of candidate routes
    # routes_df = pd.DataFrame([...])
    # print(scheduler.select_compatible_routes(routes_df))



