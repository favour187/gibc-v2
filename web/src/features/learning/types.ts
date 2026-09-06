/** API types for Adaptive Learning Studio (mirror FastAPI schemas). */

export interface SkillDTO {
  skill_id: string;
  title: string;
  track: string;
  description: string;
  concept: string;
  difficulty: number;
  prerequisites: string[];
}

export interface SkillStateDTO {
  skill_id: string;
  theta: number;
  mastery: number;
  mastered: boolean;
  encounters: number;
  correct: number;
  accuracy: number | null;
  repetition: number;
  interval_days: number;
  due_date: string;
  last_grade: number;
}

export interface Overview {
  profile: { target_skill: string };
  curriculum: {
    total_skills: number;
    tracks: string[];
    skills: SkillDTO[];
    order: string[];
  };
  progress: {
    total: number;
    mastered: number;
    in_progress: number;
    not_started: number;
    average_mastery: number;
  };
  frontier: string[];
  next_skill: string | null;
  next_skill_title: string | null;
  target_skill: string | null;
  target_reached: boolean;
  due_count: number;
  review_queue: number;
  streak: number;
  state_map: Record<string, SkillStateDTO>;
}

export interface SessionQuestion {
  question_id: string;
  skill_id: string;
  stem: string;
  options: string[];
  difficulty: number;
  source: "review" | "weak" | "new";
}

export interface SessionData {
  questions: SessionQuestion[];
  count: number;
  skill_titles: Record<string, string>;
}

export interface GradeResult {
  record: {
    correct: boolean;
    grade: number;
    theta_before: number;
    theta_after: number;
    mastery_after: number;
    interval_days_after: number;
    due_date_after: string;
  };
  question: { stem: string; correct_answer: string; explanation: string; misconception: string };
  skill: SkillStateDTO;
  skill_title: string;
}

export interface TutorResult {
  reply: string;
  provider: string;
  used_fallback: boolean;
  due_count: number;
  frontier_count: number;
}
