diff --git a/toDelete.py b/toDelete.py
index 999b326f0b38e03a8151c3714e8df01e0959ecbc..5916221d053e9f8daa1cadb24b589e47be459c43 100644
--- a/toDelete.py
+++ b/toDelete.py
@@ -26,55 +26,59 @@ class TripScheduler:
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
-        total_km = self.df['Distanza'].sum()
-        total_comp = self.df['Compenso (€)'].sum()
+        df = self.df
+        if 'Codice Viaggio' in df.columns:
+            df = df[df['Codice Viaggio'] != "TOTALE"]
+
+        total_km = df['Distanza'].sum()
+        total_comp = df['Compenso (€)'].sum()
         avg_eur_km = round(total_comp / total_km, 2) if total_km else 0
-        total_fuel = self.df['Carburante (€)'].sum()
-        total_toll = self.df['Pedaggi (€)'].sum()
+        total_fuel = df['Carburante (€)'].sum()
+        total_toll = df['Pedaggi (€)'].sum()
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
 



