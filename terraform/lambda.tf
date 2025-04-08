resource "aws_security_group" "lambda-sg" {
  name        = "fiap-hackathon-lambda-authorizer-sg"
  description = "FIAP Hackathon - Lambda Authorizer Security Group"
  vpc_id      = data.aws_vpc.selected_vpc.id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = data.aws_ip_ranges.api_gateway.cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lambda_function" "aws-lambda" {
  function_name = "fiap-hackathon-lambda-authorizer"
  description   = "FIAP Hackathon - Lambda Authorizer"
  role          = data.aws_iam_role.lab_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  filename      = "../bin/bootstrap.zip"
  vpc_config {
    subnet_ids         = [for subnet in data.aws_subnet.selected_subnets : subnet.id]
    security_group_ids = [aws_security_group.lambda-sg.id]
  }
}
