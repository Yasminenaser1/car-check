import requests

def get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

year, make, model = 2020, "toyota", "camry"

ratings = get(f"https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{make}/model/{model}")
print("SAFETY RATINGS:", ratings.get("Count"), "variants")
for v in ratings.get("Results", [])[:3]:
    print("  ", v.get("VehicleDescription"), "| id:", v.get("VehicleId"))

recalls = get(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}")
print("\nRECALLS:", recalls.get("Count"))
for r in recalls.get("results", [])[:3]:
    print("  ", r.get("Component"))

complaints = get(f"https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}")
print("\nCOMPLAINTS:", complaints.get("count"))
for c in complaints.get("results", [])[:3]:
    print("  ", c.get("components"))
