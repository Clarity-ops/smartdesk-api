import json
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def send_request(endpoint: str, method: str = "GET", data: dict = None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")

    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body) as response:
            if response.status == 204:
                return True
            content = response.read().decode("utf-8")
            return json.loads(content) if content else True
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code} on {method} {endpoint}: {error_msg}")
        return None
    except urllib.error.URLError:
        print(f"[FATAL] Cannot connect to server at {BASE_URL}. Ensure FastAPI is running!")
        exit(1)


def main():
    print("=== SmartDesk Demonstration Script ===\n")
    created_ticket_ids = []

    # 1. Health check
    health = send_request("/")
    print(f"[1] Server status: {health.get('status', 'unknown')}\n")

    # 2. Створюємо та закриваємо прецеденти (База знань)
    historical_tickets = [
        {
            "title": "Monitor display is completely black and won't turn on",
            "description": "External display stopped showing image. Solution: replaced faulty power cable and adapter.",
            "category": "Hardware",
            "priority": 2,
            "sla_hours": 24,
        },
        {
            "title": "Unauthorized SSH brute-force detected",
            "description": "Multiple failed root logins from suspicious external IP. Solution: blocked subnet on perimeter firewall.",
            "category": "Security",
            "priority": 4,
            "sla_hours": 4,
        },
        {
            "title": "Corporate VPN authentication timeout",
            "description": "User unable to connect to OpenVPN gateway. Solution: flushed DNS and renewed client SSL certificate.",
            "category": "Software",
            "priority": 2,
            "sla_hours": 48,
        },
    ]

    print("[2] Seeding resolved knowledge-base tickets...")
    for t in historical_tickets:
        created = send_request("/tickets/", method="POST", data=t)
        if created:
            created_ticket_ids.append(created["id"])
            send_request(f"/tickets/{created['id']}/status", method="PATCH", data={"status": "Closed"})
            print(f"  - Created and Closed #{created['id']}: '{t['title'][:45]}...'")
    print()

    # 3. Створюємо нові відкриті заявки
    new_tickets = [
        {
            "title": "Broken computer screen on desk 402",
            "description": "My PC display won't light up at all, power button does nothing.",
            "category": "Hardware",
            "priority": 2,
            "sla_hours": 24,
        },
        {
            "title": "Potential data breach in marketing DB",
            "description": "Database export logs show abnormal activity at 3 AM from contractor account.",
            "category": "Security",
            "priority": 4,
            "sla_hours": 2,
        },
        {
            "title": "Requesting ergonomic keyboard",
            "description": "Need vertical keyboard due to wrist strain, standard IT equipment request.",
            "category": "Hardware",
            "priority": 1,
            "sla_hours": 72,
        },
    ]

    print("[3] Registering incoming open tickets...")
    target_hardware_ticket_id = None
    for t in new_tickets:
        created = send_request("/tickets/", method="POST", data=t)
        if created:
            created_ticket_ids.append(created["id"])
            print(f"  - Created Open #{created['id']}: [{created['category']}] '{t['title']}'")
            if "screen" in t["title"]:
                target_hardware_ticket_id = created["id"]
    print()

    time.sleep(0.3)

    # 4. Демонстрація Смарт-черги (Dynamic Urgency)
    print("[4] Fetching Smart Queue (Sorted by Dynamic Urgency):")
    queue = send_request("/tickets/queue")
    if queue:
        print(f"{'ID':<4} | {'Category':<10} | {'Base Prio':<9} | {'Urgency Score':<13} | {'Title'}")
        print("-" * 75)
        for t in queue:
            urgency = t.get("dynamic_urgency", 0.0)
            print(f"{t['id']:<4} | {t['category']:<10} | {t['priority']:<9} | {urgency:<13.3f} | {t['title'][:35]}")
    print()

    # 5. Демонстрація семантичного NLP-пошуку (Cosine Similarity)
    if target_hardware_ticket_id:
        print(f"[5] Querying AI recommendations for Ticket #{target_hardware_ticket_id}:")
        print("    Original problem: 'Broken computer screen on desk 402'")
        similar = send_request(f"/tickets/{target_hardware_ticket_id}/similar?threshold=0.35")

        if similar:
            for s in similar:
                sim_pct = s["similarity"] * 100
                print(f"    --> Match Found ({sim_pct:.1f}% confidence): #{s['id']} '{s['title']}'")
                print(f"        Historical resolution: {s['description']}\n")
        else:
            print("    No relevant past solutions found.\n")

    # 6. Очищення даних (DELETE CRUD)
    print("[6] Cleaning up demonstration data via DELETE /tickets/{id}...")
    for t_id in created_ticket_ids:
        success = send_request(f"/tickets/{t_id}", method="DELETE")
        if success:
            print(f"  - Deleted Ticket #{t_id}")
    print("\nDatabase is clean. All demo artifacts removed successfully.")


if __name__ == "__main__":
    main()