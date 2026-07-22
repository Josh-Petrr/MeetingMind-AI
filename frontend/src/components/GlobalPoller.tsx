"use client";

import { useEffect } from "react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

export function GlobalPoller() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const checkPendingMeetings = async () => {
      const pendingStr = sessionStorage.getItem("pendingMeetings");
      if (!pendingStr) return;

      let pendingList: string[] = [];
      try {
        pendingList = JSON.parse(pendingStr);
      } catch (e) {
        return;
      }

      if (pendingList.length === 0) return;

      const updatedList = [...pendingList];

      for (const meetingId of pendingList) {
        try {
          const res = await fetch(`${apiUrl}/review/${meetingId}`);
          if (res.ok) {
            const json = await res.json();
            if (json.pipeline_status === "completed" || json.boris_output) {
              // Trigger global success toast
              toast.success(
                (t) => (
                  <span className="flex flex-col gap-1 cursor-pointer" onClick={() => router.push(`/review/${meetingId}`)}>
                    <b>Intelligence Extracted!</b>
                    <span className="text-sm">Click here to view report</span>
                  </span>
                ),
                { duration: 8000, icon: '🧠', style: { background: '#1e293b', color: '#fff' } }
              );
              
              // Remove from pending list
              const index = updatedList.indexOf(meetingId);
              if (index > -1) {
                updatedList.splice(index, 1);
              }
            } else if (json.pipeline_status === "error") {
              toast.error(`Processing failed for meeting: ${meetingId}`);
              const index = updatedList.indexOf(meetingId);
              if (index > -1) {
                updatedList.splice(index, 1);
              }
            }
          }
        } catch (err) {
          console.error(err);
        }
      }

      // Update session storage if changed
      if (updatedList.length !== pendingList.length) {
        sessionStorage.setItem("pendingMeetings", JSON.stringify(updatedList));
      }
    };

    interval = setInterval(checkPendingMeetings, 4000); // Check every 4 seconds

    return () => clearInterval(interval);
  }, [router, apiUrl]);

  return null;
}

