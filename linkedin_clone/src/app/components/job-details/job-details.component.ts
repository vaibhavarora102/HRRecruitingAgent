import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { JobService } from '../../services/job/job.service';
import { Job } from '../../models/job.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-job-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './job-details.component.html',
  styleUrl: './job-details.component.css'
})
export class JobDetailsComponent implements OnInit {
  selectedJob: Job | null = null;
  @Output() applyClick = new EventEmitter<void>();

  constructor(private jobService: JobService) {}

  ngOnInit(): void {
    this.jobService.selectedJob$.subscribe(job => {
      this.selectedJob = job;
    });
  }
  
  onApplyClick(): void {
    this.applyClick.emit();
  }
}
