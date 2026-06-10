"use client";

import React from "react";
import {
  Mail,
  MapPin,
  Phone,
  Link,
  Award,
  Code,
  Briefcase,
  BookOpen,
} from "lucide-react";

interface ResumeCardProps {
  content: string;
}

export function ResumeCard({ content }: ResumeCardProps) {
  const parseContent = (text: string) => {
    const cleaned = text
      .replace(/\*\*/g, "")
      .replace(/#{1,6}\s+/g, "")
      .replace(/\[(.+?)\]\((.+?)\)/g, "$1");
    return cleaned;
  };

  const extractContactInfo = (text: string) => {
    const contact = {
      name: "",
      email: "",
      phone: "",
      location: "",
      linkedin: "",
      github: "",
    };

    const emailMatch = text.match(
      /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/,
    );
    if (emailMatch) contact.email = emailMatch[0];

    const phoneMatch = text.match(/\+?[\d\s\-()]{10,}/);
    if (phoneMatch) contact.phone = phoneMatch[0].trim();

    if (text.includes("Tunis") || text.includes("Tunisia")) {
      contact.location = "Tunis, Tunisia";
    }

    const nameMatch = text.match(/^([A-Z][a-z]+\s+[A-Z][a-z]+)/m);
    if (nameMatch) contact.name = nameMatch[1];

    const linkedinMatch = text.match(/linkedin\.com\/in\/[\w\-]+/i);
    if (linkedinMatch) contact.linkedin = linkedinMatch[0];

    const githubMatch = text.match(/github\.com\/[\w\-]+/i);
    if (githubMatch) contact.github = githubMatch[0];

    return contact;
  };

  const contact = extractContactInfo(content);
  const cleaned = parseContent(content);

  const sections = cleaned.split(
    /(?=^(Education|Technical Skills|Work Experience|Projects|Additional Information))/m,
  );

  const renderSection = (section: string) => {
    const lines = section
      .split("\n")
      .filter((line) => line.trim())
      .slice(0, 20);

    return lines.map((line, idx) => {
      const trimmed = line.trim();

      if (
        /^(Education|Technical Skills|Work Experience|Projects|Additional Information)/i.test(
          trimmed,
        )
      ) {
        return (
          <h2
            key={idx}
            className="text-lg font-bold text-blue-700 mt-6 mb-4 pb-2 border-b-2 border-blue-200 flex items-center gap-2"
          >
            {trimmed.includes("Education") && <BookOpen size={20} />}
            {trimmed.includes("Technical") && <Code size={20} />}
            {trimmed.includes("Work") && <Briefcase size={20} />}
            {trimmed.includes("Projects") && <Award size={20} />}
            {trimmed}
          </h2>
        );
      }

      if (
        /^(Flask|Angular|MongoDB|AWS|LangChain|CrewAI|Spring Boot|ASP\.NET)/i.test(
          trimmed,
        ) ||
        trimmed.match(/^[A-Z][^:]*:/) ||
        (trimmed.match(/^[A-Z]/) && trimmed.length < 80 && idx > 0)
      ) {
        return (
          <h3
            key={idx}
            className="font-semibold text-gray-900 mt-3 mb-2 text-base"
          >
            {trimmed}
          </h3>
        );
      }

      if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
        return (
          <div key={idx} className="flex gap-3 mb-2 ml-4 text-gray-700">
            <span className="text-blue-600 font-bold flex-shrink-0">•</span>
            <span>{trimmed.replace(/^[•\-]\s*/, "")}</span>
          </div>
        );
      }

      if (trimmed && !trimmed.endsWith(":")) {
        return (
          <p key={idx} className="text-gray-700 mb-2 text-sm leading-relaxed">
            {trimmed}
          </p>
        );
      }

      return null;
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-8">
        <h1 className="text-4xl font-bold mb-3">
          {contact.name || "Professional Resume"}
        </h1>

        <div className="flex flex-wrap gap-4 text-sm text-blue-50">
          {contact.location && (
            <div className="flex items-center gap-2 bg-blue-500 bg-opacity-40 px-3 py-2 rounded-lg">
              <MapPin size={16} className="flex-shrink-0" />
              <span>{contact.location}</span>
            </div>
          )}
          {contact.email && (
            <a
              href={`mailto:${contact.email}`}
              className="flex items-center gap-2 bg-blue-500 bg-opacity-40 px-3 py-2 rounded-lg hover:bg-opacity-60 transition"
            >
              <Mail size={16} className="flex-shrink-0" />
              <span>{contact.email}</span>
            </a>
          )}
          {contact.phone && (
            <div className="flex items-center gap-2 bg-blue-500 bg-opacity-40 px-3 py-2 rounded-lg">
              <Phone size={16} className="flex-shrink-0" />
              <span>{contact.phone}</span>
            </div>
          )}
          {contact.linkedin && (
            <a
              href={`https://${contact.linkedin}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-blue-500 bg-opacity-40 px-3 py-2 rounded-lg hover:bg-opacity-60 transition"
            >
              <Link size={16} className="flex-shrink-0" />
              <span>LinkedIn</span>
            </a>
          )}
          {contact.github && (
            <a
              href={`https://${contact.github}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-blue-500 bg-opacity-40 px-3 py-2 rounded-lg hover:bg-opacity-60 transition"
            >
              <Link size={16} className="flex-shrink-0" />
              <span>GitHub</span>
            </a>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-8 space-y-4">
        <div className="prose prose-sm max-w-none">
          {sections.map((section, idx) => (
            <div key={idx} className="space-y-2">
              {renderSection(section)}
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-4 border-t border-gray-200">
        <p className="text-xs text-gray-600 text-center">
          Resume formatted and optimized for readability
        </p>
      </div>
    </div>
  );
}
