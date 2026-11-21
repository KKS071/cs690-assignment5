"""ADR 0001 check: 8 threads book the same slot at once, 30 trials.

    python evidence/race_check.py .

Before the change: 28 / 30 trials saved more than one overlapping booking.
After it: 0 / 30. Not a test: timing-dependent, so it is kept as evidence only.
"""
import os, sys, tempfile, threading
sys.path.insert(0, sys.argv[1])
from app.repository import Repository
from app.service import BookingService, BookingError
ok_total = 0
for trial in range(30):
    r = Repository(os.path.join(tempfile.mkdtemp(), 'r.db')); r.init_db()
    barrier = threading.Barrier(8); ok = []
    def go(i):
        s = BookingService(Repository(r.db_path)); barrier.wait()
        try: s.create_booking({"room_id":1,"date":"2031-03-14","start":"09:00","end":"10:00","booked_by":f"P{i}"}); ok.append(i)
        except BookingError: pass
    ts=[threading.Thread(target=go,args=(i,)) for i in range(8)]; [t.start() for t in ts]; [t.join() for t in ts]
    n = len(r.list_bookings("2031-03-14")); ok_total += (n > 1)
print("trials with more than one overlapping booking saved:", ok_total, "/ 30")
