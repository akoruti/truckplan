import pandas as pd
from datetime import datetime, timedelta

class TripScheduler:
    def __init__(self, fuel_consumption=3.5, fuel_price=1.69, toll_rates=None):
        """
        fuel_consumption: km per liter
        fuel_price: euro per liter
        toll_rates: dict with tuple (start, end) as key and toll cost as value
        """
        self.trips = []
        self.df = pd.DataFrame()
        self.fuel_consumption = fuel_consumption
        self.fuel_price = fuel_price
        self.toll_rates = toll_rates or {}

    def add_trip(self, codice, partenza, dt_p, destinazione, dt_a,
                 distanza_km, durata_est, compenso_eur, eur_per_km,
                 rimorchio, modalita):
        trip = {
            "Codice Viaggio": codice,
            "Partenza": partenza,
            "Data/Ora Partenza": dt_p,
            "Destinazione": destinazione,
            "Data/Ora Arrivo": dt_a,
            "Distanza": distanza_km,
            "Durata stimata": durata_est,
            "Compenso (€)": compenso_eur,
            "€/km": eur_per_km,
            "Rimorchio": rimorchio,
            "Modalità": modalita
        }
        self.trips.append(trip)
        self._update_df()

    def _update_df(self):
        self.df = pd.DataFrame(self.trips)

    def compute_costs(self):
        def fuel_cost(km):
            liters = km / self.fuel_consumption
            return round(liters * self.fuel_price, 2)
        def toll_cost(row):
            key = (row['Partenza'], row['Destinazione'])
            return self.toll_rates.get(key, 0.0)
        self.df['Carburante (€)'] = self.df['Distanza'].apply(fuel_cost)
        self.df['Pedaggi (€)'] = self.df.apply(toll_cost, axis=1)
        self.df['Totale costi (€)'] = self.df['Carburante (€)'] + self.df['Pedaggi (€)']

    def compute_totals(self):
        total_km = self.df['Distanza'].sum()
        total_comp = self.df['Compenso (€)'].sum()
        avg_eur_km = round(total_comp / total_km, 2) if total_km else 0
        total_fuel = self.df['Carburante (€)'].sum()
        total_toll = self.df['Pedaggi (€)'].sum()
        total_costs = total_fuel + total_toll
        return {
            "TOTALE": {
                "Distanza": total_km,
                "Compenso (€)": total_comp,
                "€/km": avg_eur_km,
                "Carburante (€)": total_fuel,
                "Pedaggi (€)": total_toll,
                "Totale costi (€)": total_costs
            }
        }

    def append_totals_row(self):
        totals = self.compute_totals()["TOTALE"]
        totals_row = {"Codice Viaggio": "TOTALE"}
        for k, v in totals.items():
            totals_row[k] = v
        for col in self.df.columns:
            if col not in totals_row:
                totals_row[col] = ""
        self.df = pd.concat([self.df, pd.DataFrame([totals_row])], ignore_index=True)

    def save_csv(self, path):
        self.df.to_csv(path, index=False)

    def next_available(self, last_arrival_str, unload_min=45, rest_h=11):
        last_arrival = datetime.strptime(last_arrival_str, "%Y-%m-%d %H:%M")
        end_unload = last_arrival + timedelta(minutes=unload_min)
        available = end_unload + timedelta(hours=rest_h)
        return available

    def select_compatible_routes(self, routes_df, available_time, 
                                 min_eur_km=None, min_comp=None, min_dist=None, top_n=5):
        """
        Filtra le rotte disponibili in base alla disponibilità dell'autista e ai criteri
        parameters:
            routes_df: DataFrame con colonne ['Partenza','Data/Ora Partenza','Destinazione','Distanza','Compenso (€)','€/km',...]
            available_time: datetime quando l'autista è libero
            min_eur_km: filtro minimo €/km
            min_comp: filtro minimo compenso
            min_dist: filtro minimo distanza in km
            top_n: numero di rotte da restituire
        returns:
            DataFrame con le prime top_n rotte compatibili ordinate per compenso poi €/km
        """
        df = routes_df.copy()
        df['Data/Ora Partenza'] = pd.to_datetime(df['Data/Ora Partenza'], format="%Y-%m-%d %H:%M")
        df = df[df['Data/Ora Partenza'] >= available_time]
        if min_eur_km is not None:
            df = df[df['€/km'] >= min_eur_km]
        if min_comp is not None:
            df = df[df['Compenso (€)'] >= min_comp]
        if min_dist is not None:
            df = df[df['Distanza'] >= min_dist]
        df = df.sort_values(by=['Compenso (€)','€/km'], ascending=False)
        return df.head(top_n)


