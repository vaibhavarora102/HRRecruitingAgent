import { CommonModule } from '@angular/common';
import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Application } from '../../models/application.model';
import { JobService } from '../../services/job/job.service';
import { Job } from '../../models/job.model';

@Component({
  selector: 'app-application-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './application-modal.component.html',
  styleUrl: './application-modal.component.css'
})
export class ApplicationModalComponent implements OnInit {
  selectedJob: Job | null = null;
  @Output() close = new EventEmitter<void>();

  resumeFile: File | null = null;
  resumeTouched = false;
  resumeUploaded = false;

  formData = {
    name: '',
    email: '',
    phone: '',
    resume_url: ''
  };

  constructor(private jobService: JobService) {}

  ngOnInit(): void {
    this.jobService.selectedJob$.subscribe(job => {
      this.selectedJob = job;
    });
  }

  isFormValid(): boolean {
    return !!(
      this.formData.name.trim() &&
      this.formData.email.trim() &&
      this.formData.phone.trim() &&
      this.resumeFile && // file selected
      this.isValidEmail(this.formData.email)
    );
  }

  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.resumeFile = input.files?.[0] ?? null;
    this.resumeTouched = true;
    this.resumeUploaded = false;
  }

  async submitApplication(): Promise<void> {
    if (!this.selectedJob || !this.isFormValid()) return;

    try {
      // 1. Upload resume here when user submits
      if (this.resumeFile && this.formData.email) {
        const url = await this.jobService.uploadResume(
          this.resumeFile,
          this.formData.email,
          this.selectedJob.id.toString()
        );
        if (!url) throw new Error('Resume upload failed');
        this.formData.resume_url = url;
        this.resumeUploaded = true;
      }

      // 2. Prepare application object
      const application: Application = {
        job_id: this.selectedJob.id,
        ...this.formData
      };

      // 3. Save application in Supabase
      const success = await this.jobService.submitApplication(application);
      if (success) {
        alert(`Application submitted successfully for ${this.selectedJob.title}!`);
        this.resetForm();
        this.close.emit();
      }
    } catch (error) {
      console.error(error);
      alert('Failed to submit application. Please try again.');
    }
  }

  onCancel(): void {
    this.resetForm();
    this.close.emit();
  }

  onOverlayClick(event: MouseEvent): void {
    this.onCancel();
  }

  resetForm(): void {
    this.formData = {
      name: '',
      email: '',
      phone: '',
      resume_url: ''
    };
    this.resumeFile = null;
    this.resumeUploaded = false;
    this.resumeTouched = false;
  }
}