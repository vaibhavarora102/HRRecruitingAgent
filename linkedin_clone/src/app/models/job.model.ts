export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  type: string;
  salary: string;
  posted: string;
  applicants: number;
  description: string;
  requirements: string[];
  logo: string;
}