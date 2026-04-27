export interface SearchItem {
  uid: string;
  name: string;
  type: "person" | "event" | "place";
  score: number;
}
