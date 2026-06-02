export interface TopologyNode {
  id: string;
  label: string;
  kind: string;
  role: string | null;
  image: string | null;
  status: string | null;
  management_ipv4: string | null;
  container_name: string | null;
  metadata: Record<string, unknown>;
}

export interface TopologyLink {
  id: string;
  source: string;
  target: string;
  source_interface: string | null;
  target_interface: string | null;
  label: string;
  subnet: string | null;
}

export interface Topology {
  nodes: TopologyNode[];
  links: TopologyLink[];
  warnings: string[];
}
