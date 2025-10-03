import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ApplicationModalComponent } from './components/application-modal/application-modal.component';
import { JobDetailsComponent } from './components/job-details/job-details.component';
import { JobListComponent } from './components/job-list/job-list.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    CommonModule,
    NavbarComponent,
    JobListComponent,
    JobDetailsComponent,
    ApplicationModalComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'linkedin_clone';
  showApplicationModal = false;
}
