import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Job } from '../../models/job.model';
import { Application } from '../../models/application.model';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable({
  providedIn: 'root'
})
export class JobService {
  private jobsSubject = new BehaviorSubject<Job[]>([]);
  private selectedJobSubject = new BehaviorSubject<Job | null>(null);
  private applicationsSubject = new BehaviorSubject<Application[]>([]);

  jobs$ = this.jobsSubject.asObservable();
  selectedJob$ = this.selectedJobSubject.asObservable();
  applications$ = this.applicationsSubject.asObservable();

  constructor(private supabaseService: SupabaseService) {}

  /** 🔹 Fetch all jobs from Supabase */
  async loadJobs(): Promise<void> {
    const { data, error } = await this.supabaseService.client
      .from('jobs')
      .select('*');

    if (error) {
      console.error('Error fetching jobs:', error.message);
      return;
    }

    data.map(job => job.applicants = this.getApplicants());

    this.jobsSubject.next(data as Job[]);
  }

  private getApplicants(){
    const randomNumber = Math.floor(Math.random() * 100);
    return randomNumber;
  }

  /** 🔹 Select a job for modal */
  selectJob(job: Job): void {
    this.selectedJobSubject.next(job);
  }

  /** 🔹 Upload resume file and return URL */
  async uploadResume(file: File, userEmail: string, job_id: string): Promise<string | null> {
    const filePath = `${job_id}/${userEmail}-${Date.now()}-${file.name}`;

    const { error } = await this.supabaseService.client.storage
      .from('resumes')
      .upload(filePath, file);

    if (error) {
      console.error('Resume upload failed:', error.message);
      return null;
    }

    // get public URL (if bucket is public)
    return this.supabaseService.getPublicUrl('resumes', filePath);
  }

  /** 🔹 Submit job application to Supabase */
  async submitApplication(application: Application): Promise<boolean> {
    const { data, error } = await this.supabaseService.client
      .from('applications')
      .insert([application]);

    if (error) {
      console.error('Error submitting application:', error.message);
      return false;
    }

    // update local BehaviorSubject
    const currentApps = this.applicationsSubject.value;
    this.applicationsSubject.next([...currentApps, application]);
    return true;
  }
}