/** Typed API calls for Adaptive Learning Studio. */
import { api } from "../../lib/api";
import type { GradeResult, Overview, SessionData, TutorResult } from "./types";

export const learningApi = {
  overview: () => api<Overview>("/learning/overview"),
  session: () => api<SessionData>("/learning/session"),
  grade: (question_id: string, chosen_index: number, self_rating?: number) =>
    api<GradeResult>("/learning/grade", {
      method: "POST",
      body: { question_id, chosen_index, self_rating: self_rating ?? null },
    }),
  finish: (question_count: number, correct_count: number) =>
    api<unknown>("/learning/session/finish", {
      method: "POST",
      body: { question_count, correct_count },
    }),
  tutor: (message: string, question_id?: string) =>
    api<TutorResult>("/learning/tutor", {
      method: "POST",
      body: { message, question_id: question_id ?? null },
    }),
  setTarget: (skill_id: string) =>
    api<{ target_skill: string; title: string }>("/learning/target", {
      method: "PATCH",
      body: { skill_id },
    }),
};
