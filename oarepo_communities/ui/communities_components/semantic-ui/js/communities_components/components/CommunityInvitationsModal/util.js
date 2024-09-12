import * as Yup from "yup";

export const emailHasDisplayName = (email) =>
  email.includes("<") && email.includes(">");

export const parseDisplayName = (email) => email.split("<")[0].trim();

export const serializeMembers = (emails) =>
  emails.map((email) => ({
    type: "email",
    id: email,
  }));

const re = new RegExp(/\n/, "g");

export const findAndValidateEmails = (value) => {
  const validEmails = [];
  const invalidEmails = [];
  const emailSchema = Yup.string().email();
  if (!value) {
    return { validEmails, invalidEmails };
  }
  const emailsArray = value.split(re).map((e) => e.trim());
  for (const email of emailsArray) {
    if (!email) {
      continue;
    }
    let processedEmail = email;

    if (emailHasDisplayName(email)) {
      processedEmail = processedEmail.match(/<([^<>]+)>/)[1].trim();
    }
    if (emailSchema.isValidSync(processedEmail)) {
      const emailExists = validEmails.some((mail) =>
        mail.includes(processedEmail)
      );

      if (!emailExists) {
        validEmails.push(email);
      }
    } else {
      invalidEmails.push(email);
    }
  }

  return { validEmails, invalidEmails };
};
