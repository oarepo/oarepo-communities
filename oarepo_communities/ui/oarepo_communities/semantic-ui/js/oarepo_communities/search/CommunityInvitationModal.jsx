import React from "react";
import { Modal, Button, Form, Icon, Message } from "semantic-ui-react";
import { i18next } from "@translations/oarepo_communities";

export const CommunityInvitationModal = ({
  open,
  onClose,
  onSubmit,
  error,
}) => {
  const [email, setEmail] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    await onSubmit(email);
    setLoading(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="tiny"
      trigger={
        <Button
          className="fluid-responsive"
          content={i18next.t("Invite...")}
          positive
          fluid
          compact
          icon="user plus"
          labelPosition="left"
          aria-expanded={open}
          aria-haspopup="dialog"
        />
      }
    >
      <Modal.Header>Invite user to the community</Modal.Header>
      <Modal.Content>
        <Form error={!!error}>
          <Form.Input
            fluid
            icon="user"
            iconPosition="left"
            placeholder="Email"
            value={email}
            onChange={(e, { value }) => setEmail(value)}
          />
          <Message error header="Error" content={error} />
        </Form>
        <div>dwadwa</div>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={onClose}>
          <Icon name="remove" /> Cancel
        </Button>
        <Button primary onClick={handleSubmit} loading={loading}>
          <Icon name="checkmark" /> Invite
        </Button>
      </Modal.Actions>
    </Modal>
  );
};
