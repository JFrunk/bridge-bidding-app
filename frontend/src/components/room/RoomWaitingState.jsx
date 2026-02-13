/**
 * RoomWaitingState - Standardized Table: Returns null
 *
 * P0: Guest enters code → sees standard table view immediately
 * The RoomStatusBar shows "Waiting for Host to Deal" status.
 * No separate waiting overlay needed.
 */

export default function RoomWaitingState() {
  // Standardized Table: Don't show a waiting overlay
  // The standard table view with RoomStatusBar provides all needed info
  return null;
}
