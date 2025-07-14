"""Utility class for scheduling truck trips and analyzing driver availability."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

import pandas as pd


@dataclass
class Trip:
    code: str
    origin: str
    departure: str  # "YYYY-MM-DD HH:MM"
    destination: str
    arrival: str    # "YYYY-MM-DD HH:MM"
    distance: float
    duration: str
    payout: float
    euro_per_km: float
    trailer: str
    mode: str
    fuel_cost: Optional[float] = None
    toll_cost: Optional[float] = None
    total_cost: Optional[float] = None


class TripScheduler:
    """Manage trips for a driver and compute costs and availability."""

    def __init__(self, fuel_consumption: float = 3.5, fuel_price: float = 1.69,
                 toll_rates: Optional[Dict[Tuple[str, str], float]] = None) -> None:
        self.trips: list[Trip] = []
        self.fuel_consumption = fuel_consumption
        self.fuel_price = fuel_price
        self.toll_rates = toll_rates or {}

    def add_trip(self, trip: Trip) -> None:
        """Add a new trip to the schedule."""
        self.trips.append(trip)

    def _to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([t.__dict__ for t in self.trips])

    def compute_costs(self) -> pd.DataFrame:
        """Calculate fuel and toll costs for each trip."""
        df = self._to_dataframe()

        def fuel(km: float) -> float:
            liters = km / self.fuel_consumption
            return round(liters * self.fuel_price, 2)

        df['Carburante (€)'] = df['distance'].apply(fuel)

        def toll(row: pd.Series) -> float:
            key = (row['origin'], row['destination'])
            return self.toll_rates.get(key, 0.0)

        df['Pedaggi (€)'] = df.apply(toll, axis=1)
        df['Totale costi (€)'] = df['Carburante (€)'] + df['Pedaggi (€)']

        for i, t in enumerate(self.trips):
            t.fuel_cost = float(df.loc[i, 'Carburante (€)'])
            t.toll_cost = float(df.loc[i, 'Pedaggi (€)'])
            t.total_cost = float(df.loc[i, 'Totale costi (€)'])
        return df

    def append_totals_row(self, df: pd.DataFrame) -> pd.DataFrame:
        """Append a total row summarizing numeric columns."""
        numeric_cols = ['distance', 'payout', 'euro_per_km',
                        'Carburante (€)', 'Pedaggi (€)', 'Totale costi (€)']
        totals = {c: df[c].sum() for c in numeric_cols if c in df}
        if totals.get('distance'):
            totals['euro_per_km'] = round(totals['payout'] / totals['distance'], 2)
        row = {col: '' for col in df.columns}
        row['code'] = 'TOTALE'
        row.update(totals)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        return df

    def save_csv(self, path: str) -> None:
        """Save the current schedule with costs and totals to CSV."""
        df = self.compute_costs()
        df = self.append_totals_row(df)
        df.to_csv(path, index=False)

    def next_available(self, last_arrival: str, unload_minutes: int = 45,
                       rest_hours: int = 11) -> datetime:
        """Return the next available datetime after unloading and rest."""
        end = datetime.strptime(last_arrival, "%Y-%m-%d %H:%M")
        end += timedelta(minutes=unload_minutes)
        return end + timedelta(hours=rest_hours)

    def select_compatible_routes(
        self,
        routes: pd.DataFrame,
        available_time: datetime,
        min_euro_km: float | None = None,
        min_payout: float | None = None,
        min_distance: float | None = None,
        top_n: int = 5,
    ) -> pd.DataFrame:
        """Filter and sort routes that start after available_time."""
        df = routes.copy()
        df['Data/Ora Partenza'] = pd.to_datetime(df['Data/Ora Partenza'])
        df = df[df['Data/Ora Partenza'] >= available_time]
        if min_euro_km is not None:
            df = df[df['€/km'] >= min_euro_km]
        if min_payout is not None:
            df = df[df['Compenso (€)'] >= min_payout]
        if min_distance is not None:
            df = df[df['Distanza'] >= min_distance]
        df = df.sort_values(by=['Compenso (€)', '€/km'], ascending=False)
        return df.head(top_n)


def main() -> None:
    import streamlit as st

    st.title("Trip Scheduler")

    if "scheduler" not in st.session_state:
        st.session_state.scheduler = TripScheduler()

    scheduler: TripScheduler = st.session_state.scheduler

    with st.expander("Add new trip"):
        with st.form("trip_form"):
            code = st.text_input("Code")
            origin = st.text_input("Origin")
            departure = st.text_input("Departure (YYYY-MM-DD HH:MM)")
            destination = st.text_input("Destination")
            arrival = st.text_input("Arrival (YYYY-MM-DD HH:MM)")
            distance = st.number_input("Distance (km)", min_value=0.0)
            duration = st.text_input("Duration")
            payout = st.number_input("Payout (€)", min_value=0.0)
            euro_km = st.number_input("€/km", min_value=0.0)
            trailer = st.text_input("Trailer")
            mode = st.text_input("Mode")
            submit = st.form_submit_button("Add trip")
            if submit:
                scheduler.add_trip(
                    Trip(
                        code=code,
                        origin=origin,
                        departure=departure,
                        destination=destination,
                        arrival=arrival,
                        distance=distance,
                        duration=duration,
                        payout=payout,
                        euro_per_km=euro_km,
                        trailer=trailer,
                        mode=mode,
                    )
                )
                st.success("Trip added")

    if scheduler.trips:
        df = scheduler.compute_costs()
        df = scheduler.append_totals_row(df)
        st.subheader("Schedule")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "schedule.csv", "text/csv")

        last_trip = scheduler.trips[-1]
        next_time = scheduler.next_available(last_trip.arrival)
        st.info(f"Next available after: {next_time:%Y-%m-%d %H:%M}")

        st.subheader("Check compatible routes")
        upload = st.file_uploader("Upload routes CSV", type=["csv"])
        if upload is not None:
            routes = pd.read_csv(upload)
            compatible = scheduler.select_compatible_routes(routes, next_time)
            st.dataframe(compatible)


if __name__ == "__main__":
    main()
