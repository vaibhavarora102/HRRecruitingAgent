import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Job } from '../../models/job.model';
import { JobService } from '../../services/job/job.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-job-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './job-list.component.html',
  styleUrl: './job-list.component.css'
})
export class JobListComponent implements OnInit, OnDestroy {
  jobs: Job[] = [];
  selectedJob: Job | null = null;
  private sub = new Subscription();

  constructor(private jobService: JobService) {}

  async ngOnInit() {
    await this.jobService.loadJobs();

    this.sub.add(
      this.jobService.jobs$.subscribe(jobs => {
        this.jobs = jobs;
      })
    );

    this.sub.add(
      this.jobService.selectedJob$.subscribe(job => {
        this.selectedJob = job;
      })
    );
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  selectJob(job: Job): void {
    this.jobService.selectJob(job);
  }

  getJobClasses(job: Job): string {
    return this.selectedJob?.id === job.id 
      ? 'bg-blue-50 border-l-4 border-blue-600' 
      : '';
  }
}

