export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  type: string;
  salary: string;  
  description: string;
  requirements: string[];
  posted: Date;
  applicants: number;
}