def reverse_letters(s):
    return s[::-1]


if __name__ == "__main__":
    # Example usage
    input_string = input("Enter a string to reverse: ")
    reversed_string = reverse_letters(input_string)
    print(f"Original: {input_string}")
    print(f"Reversed: {reversed_string}")
