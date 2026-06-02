export interface ConsoleNode {
  id: string;
  name: string;
  kind: string;
  status: string;
  management_ipv4: string | null;
  console_type: string;
}

export interface ConsoleNodesResponse {
  nodes: ConsoleNode[];
}

export interface ConsoleResult {
  status: string;
  command: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
}
