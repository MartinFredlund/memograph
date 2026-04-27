export interface GraphNode {
  uid: string;
  type: "Person" | "Event" | "Place";
  name: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  social_type: string | null;
  explicit: boolean | null;
  derived: boolean | null;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
